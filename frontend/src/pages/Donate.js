import { useState } from "react";
import { useLang } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";
import translations from "../data/translations";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { Heart, ShieldCheck, IndianRupee, CheckCircle, Mail, ArrowLeft, Download } from "lucide-react";
import { toast } from "sonner";

const PRESET_AMOUNTS = [500, 1000, 2500, 5000, 10000, 25000];

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (document.getElementById("razorpay-script")) { resolve(true); return; }
    const script = document.createElement("script");
    script.id = "razorpay-script";
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function Donate() {
  const { lang } = useLang();
  const { user } = useAuth();
  const t = translations[lang].donate;

  const [form, setForm] = useState({
    name: user?.name || "", email: user?.email || "", phone: user?.phone || "",
    amount: "", pan_number: user?.pan_number || "", aadhaar_number: user?.aadhaar_number || "",
    address: user?.address || "", message: "",
  });
  const [customAmount, setCustomAmount] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null); // null | { donation }
  const [otpStep, setOtpStep] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpToken, setOtpToken] = useState("");
  const [otpDebug, setOtpDebug] = useState(null);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const selectAmount = (amt) => { setForm({ ...form, amount: String(amt) }); setCustomAmount(false); };

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const handleSendOtp = async () => {
    setSubmitting(true);
    try {
      const { data } = await api.post("/auth/send-otp", { email: form.email, purpose: "donation" });
      toast.success(data.message);
      if (data.otp_debug) setOtpDebug(data.otp_debug);
      setOtpStep(true);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setSubmitting(false); }
  };

  const handleVerifyOtp = async () => {
    setSubmitting(true);
    try {
      const { data } = await api.post("/auth/verify-otp", { email: form.email, otp, purpose: "donation" });
      setOtpToken(data.otp_token);
      toast.success("Email verified!");
      setOtpStep(false);
      submitDonation(data.otp_token);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
      setSubmitting(false);
    }
  };

  const submitDonation = async (token) => {
    try {
      const payload = { ...form, amount: parseInt(form.amount, 10), otp_token: token || otpToken || undefined };
      const { data } = await api.post("/donations/create-order", payload);
      if (data.razorpay_order_id) {
        const loaded = await loadRazorpayScript();
        if (!loaded) { toast.error("Failed to load payment gateway."); setSubmitting(false); return; }
        const options = {
          key: data.razorpay_key, amount: data.amount, currency: data.currency,
          name: "Heroic HIFI Foundation", description: "Donation",
          order_id: data.razorpay_order_id,
          handler: async (response) => {
            try {
              await api.post("/donations/verify-payment", { ...response, donation_id: data.donation.id });
              toast.success(lang === "hi" ? "दान सफल!" : "Donation successful!");
              setSuccess({ donation: { ...data.donation, status: "confirmed" } });
            } catch { toast.error("Payment verification failed."); }
            setSubmitting(false);
          },
          prefill: { name: form.name, email: form.email, contact: form.phone },
          theme: { color: "#1E56A0" },
          modal: { ondismiss: () => setSubmitting(false) },
        };
        new window.Razorpay(options).open();
      } else {
        toast.success(data.message || "Donation recorded.");
        setSuccess({ donation: data.donation });
        setSubmitting(false);
      }
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
      setSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.phone || !form.amount || !form.pan_number) {
      toast.error("Please fill all required fields including PAN number.");
      return;
    }
    setSubmitting(true);
    if (user) {
      submitDonation(null);
    } else {
      handleSendOtp();
    }
  };

  const handleDownloadCertificate = () => {
    if (success?.donation?.id) {
      window.open(`${backendUrl}/api/donations/${success.donation.id}/certificate`, "_blank");
    }
  };

  if (success) {
    return (
      <div data-testid="donate-page">
        <section className="relative py-24 sm:py-32 bg-gradient-to-br from-[#1E56A0] to-[#28A9E2]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-6">
              <Heart className="w-8 h-8 text-white" />
            </motion.div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.title}</h1>
          </div>
        </section>
        <section className="py-20 sm:py-28">
          <div className="max-w-lg mx-auto px-4 sm:px-6 text-center">
            <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}>
              <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-semibold text-[#0D2847] mb-3" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {lang === "hi" ? "आपका हृदय से धन्यवाद!" : "Thank You for Your Generosity!"}
              </h2>
              <p className="text-slate-500 mb-8">{lang === "hi" ? "आपका दान दर्ज हो गया है।" : "Your donation has been recorded."}</p>
              {success.donation?.pan_number && (
                <Button onClick={handleDownloadCertificate} className="bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full px-8 py-3 mb-4 gap-2" data-testid="download-certificate-btn">
                  <Download className="w-4 h-4" /> {lang === "hi" ? "80G प्रमाणपत्र डाउनलोड करें" : "Download 80G Certificate (PDF)"}
                </Button>
              )}
              <br />
              <Button onClick={() => { setSuccess(null); setForm({ name: user?.name || "", email: user?.email || "", phone: user?.phone || "", amount: "", pan_number: user?.pan_number || "", aadhaar_number: user?.aadhaar_number || "", address: user?.address || "", message: "" }); }} variant="outline" className="rounded-full px-8 py-3 mt-2" data-testid="donate-again-btn">
                {lang === "hi" ? "पुनः दान करें" : "Donate Again"}
              </Button>
            </motion.div>
          </div>
        </section>
      </div>
    );
  }

  if (otpStep) {
    return (
      <div data-testid="donate-page">
        <section className="relative py-24 sm:py-32 bg-gradient-to-br from-[#1E56A0] to-[#28A9E2]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-6">
              <Heart className="w-8 h-8 text-white" />
            </motion.div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.title}</h1>
          </div>
        </section>
        <section className="py-16 sm:py-24">
          <div className="max-w-md mx-auto px-4 sm:px-6 text-center">
            <button onClick={() => setOtpStep(false)} className="flex items-center gap-1 text-sm text-slate-500 hover:text-[#1E56A0] mb-6 mx-auto" data-testid="back-to-donate-form">
              <ArrowLeft className="w-4 h-4" /> Back to form
            </button>
            <div className="w-14 h-14 rounded-full bg-[#1E56A0]/10 flex items-center justify-center mx-auto mb-4">
              <Mail className="w-7 h-7 text-[#1E56A0]" />
            </div>
            <h2 className="text-2xl font-semibold text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Verify Your Email</h2>
            <p className="text-sm text-slate-500 mb-6">OTP sent to <strong className="text-[#0D2847]">{form.email}</strong></p>
            {otpDebug && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4">
                <p className="text-xs text-amber-700">Resend API key not set. Debug OTP:</p>
                <p className="text-2xl font-bold text-amber-800 tracking-[0.3em] mt-1" data-testid="donate-debug-otp">{otpDebug}</p>
              </div>
            )}
            <Input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="000000" maxLength={6}
              className="rounded-xl text-center text-2xl tracking-[0.3em] font-semibold mb-4" data-testid="donate-otp-input" />
            <Button onClick={handleVerifyOtp} disabled={submitting} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3" data-testid="donate-verify-otp-btn">
              {submitting ? "Verifying..." : "Verify & Proceed to Donate"}
            </Button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div data-testid="donate-page">
      <section className="relative py-24 sm:py-32 bg-gradient-to-br from-[#1E56A0] to-[#28A9E2]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-6">
            <Heart className="w-8 h-8 text-white" />
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.title}</motion.h1>
          <p className="text-base sm:text-lg text-blue-100 max-w-2xl mx-auto">{t.subtitle}</p>
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          {user && (
            <div className="bg-green-50 border border-green-200 rounded-2xl p-4 mb-6 flex items-start gap-3" data-testid="logged-in-notice">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 shrink-0" />
              <p className="text-sm text-green-800">Logged in as <strong>{user.name}</strong>. Your profile details are pre-filled. Email verification skipped.</p>
            </div>
          )}
          <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 mb-8 flex items-start gap-3" data-testid="razorpay-note">
            <ShieldCheck className="w-5 h-5 text-[#1E56A0] mt-0.5 shrink-0" />
            <p className="text-sm text-[#0D2847]">{t.note}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" data-testid="donation-form">
            <div>
              <Label className="text-sm font-medium text-slate-700">{t.name} *</Label>
              <Input name="name" value={form.name} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-name-input" required />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-slate-700">{t.email} *</Label>
                <Input name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-email-input" required readOnly={!!user} />
              </div>
              <div>
                <Label className="text-sm font-medium text-slate-700">{t.phone} *</Label>
                <Input name="phone" value={form.phone} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-phone-input" required />
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium text-slate-700 mb-3 block">{t.preset_amounts}</Label>
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 mb-3">
                {PRESET_AMOUNTS.map((amt) => (
                  <button type="button" key={amt} onClick={() => selectAmount(amt)}
                    className={`py-3 px-4 rounded-xl text-sm font-medium border transition-all ${form.amount === String(amt) && !customAmount ? "bg-[#1E56A0] text-white border-[#1E56A0]" : "bg-white text-slate-700 border-sky-100 hover:border-[#1E56A0]/30"}`}
                    data-testid={`donate-amount-${amt}`}
                  >
                    <IndianRupee className="w-3 h-3 inline -mt-0.5" />{amt.toLocaleString("en-IN")}
                  </button>
                ))}
                <button type="button" onClick={() => { setCustomAmount(true); setForm({ ...form, amount: "" }); }}
                  className={`py-3 px-4 rounded-xl text-sm font-medium border transition-all ${customAmount ? "bg-[#1E56A0] text-white border-[#1E56A0]" : "bg-white text-slate-700 border-sky-100"}`}
                  data-testid="donate-custom-amount-btn">{t.custom}</button>
              </div>
              {customAmount && <Input name="amount" type="number" placeholder={t.amount} value={form.amount} onChange={handleChange} className="rounded-xl" data-testid="donate-custom-amount-input" />}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-slate-700">{t.pan} *</Label>
                <Input name="pan_number" value={form.pan_number} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-pan-input" placeholder="ABCDE1234F" required />
                <p className="text-xs text-slate-400 mt-1">Mandatory for 80G provisional certificate (50% rebate)</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-slate-700">Aadhaar Number</Label>
                <Input name="aadhaar_number" value={form.aadhaar_number} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-aadhaar-input" placeholder="1234 5678 9012" />
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium text-slate-700">Address</Label>
              <Input name="address" value={form.address} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-address-input" />
            </div>

            <div>
              <Label className="text-sm font-medium text-slate-700">{t.message}</Label>
              <Textarea name="message" value={form.message} onChange={handleChange} rows={3} className="mt-1.5 rounded-xl" data-testid="donate-message-input" />
            </div>

            <Button type="submit" disabled={submitting}
              className="w-full bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
              data-testid="donate-submit-btn"
            >
              {submitting ? "Processing..." : user ? t.submit : "Verify Email & Donate"}
            </Button>
          </form>
        </div>
      </section>
    </div>
  );
}
