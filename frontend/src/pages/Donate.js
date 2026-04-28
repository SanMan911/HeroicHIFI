import { useState, useEffect } from "react";
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
  const [recurring, setRecurring] = useState(false);
  const [recurringPlan, setRecurringPlan] = useState("monthly");
  const [customRecurring, setCustomRecurring] = useState(false);
  const [customSubAmount, setCustomSubAmount] = useState(500);
  const [customInterval, setCustomInterval] = useState("monthly");
  const [coverFee, setCoverFee] = useState(false);

  // Razorpay charges roughly 2% + 18% GST = effective 2.36%. We round up.
  const computeFee = amt => (coverFee ? Math.ceil((Number(amt) || 0) * 0.0236) : 0);
  const oneTimeFee = computeFee(form.amount || 0);
  const subFee = computeFee(customSubAmount || 0);
  const RECURRING_PLANS = [
    { key: "monthly", amount: 100, en: "Monthly", hi: "मासिक", cycles: 12, sub: "₹100 / month" },
    { key: "quarterly", amount: 275, en: "Quarterly", hi: "त्रैमासिक", cycles: 4, sub: "₹275 every 3 months" },
    { key: "half_yearly", amount: 525, en: "Half-Yearly", hi: "अर्धवार्षिक", cycles: 2, sub: "₹525 every 6 months" },
    { key: "annual", amount: 1000, en: "Annual", hi: "वार्षिक", cycles: 1, sub: "₹1000 / year" },
  ];
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);
  const [otpStep, setOtpStep] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpToken, setOtpToken] = useState("");
  const [otpDebug, setOtpDebug] = useState(null);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const selectAmount = (amt) => { setForm({ ...form, amount: String(amt) }); setCustomAmount(false); };

  // Hydrate form from user when AuthContext resolves async (fixes direct-load case)
  useEffect(() => {
    if (user) {
      setForm(prev => ({
        ...prev,
        name: prev.name || user.name || "",
        email: prev.email || user.email || "",
        phone: prev.phone || user.phone || "",
        pan_number: prev.pan_number || user.pan_number || "",
        aadhaar_number: prev.aadhaar_number || user.aadhaar_number || "",
        address: prev.address || user.address || "",
      }));
    }
  }, [user]);

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
      toast.success(t.verify_email);
      setOtpStep(false);
      submitDonation(data.otp_token);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
      setSubmitting(false);
    }
  };

  const submitDonation = async (token) => {
    try {
      if (recurring) {
        if (!user) { toast.error("Please log in to set up recurring donations"); setSubmitting(false); return; }
        const subPayload = {
          plan: customRecurring ? `custom_${customInterval}` : recurringPlan,
          name: form.name, email: form.email, phone: form.phone,
          pan_number: form.pan_number, address: form.address || "",
          ...(customRecurring ? { custom_amount: parseInt(customSubAmount) || 0, cover_fee: coverFee } : {}),
        };
        if (customRecurring && (!subPayload.custom_amount || subPayload.custom_amount < 100)) {
          toast.error("Custom recurring amount must be at least \u20B9 100 per cycle.");
          setSubmitting(false); return;
        }
        const { data } = await api.post("/subscriptions/create", subPayload);
        if (data.short_url) {
          window.open(data.short_url, "_blank");
          toast.success(`Recurring donation set up! Complete authorization in the new tab.`);
        } else {
          toast.success(`Recurring donation request recorded. ${data.note || "Razorpay activation pending."}`);
        }
        setSuccess({ donation: { ...data.subscription, recurring: true } });
        setSubmitting(false);
        return;
      }
      const payload = { ...form, amount: parseInt(form.amount, 10), otp_token: token || otpToken || undefined, cover_fee: coverFee };
      const { data } = await api.post("/donations/create-order", payload);
      if (data.razorpay_order_id) {
        const loaded = await loadRazorpayScript();
        if (!loaded) { toast.error(t.gateway_fail); setSubmitting(false); return; }
        const options = {
          key: data.razorpay_key, amount: data.amount, currency: data.currency,
          name: "Heroic HIFI Foundation", description: "Donation",
          order_id: data.razorpay_order_id,
          handler: async (response) => {
            try {
              await api.post("/donations/verify-payment", { ...response, donation_id: data.donation.id });
              toast.success(t.success);
              setSuccess({ donation: { ...data.donation, status: "confirmed" } });
            } catch { toast.error(t.payment_fail); }
            setSubmitting(false);
          },
          prefill: { name: form.name, email: form.email, contact: form.phone },
          theme: { color: "#1E56A0" },
          modal: { ondismiss: () => setSubmitting(false) },
        };
        new window.Razorpay(options).open();
      } else {
        toast.success(data.message || t.recorded);
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
    const requiresAmount = !recurring;
    if (!form.name || !form.email || !form.phone || !form.pan_number || (requiresAmount && !form.amount)) {
      toast.error(t.fill_required_pan);
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
                {t.thank_you}
              </h2>
              <p className="text-slate-500 mb-8">{t.recorded}</p>
              {success.donation?.pan_number && (
                <Button onClick={handleDownloadCertificate} className="bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full px-8 py-3 mb-4 gap-2" data-testid="download-certificate-btn">
                  <Download className="w-4 h-4" /> {t.download_cert}
                </Button>
              )}
              <br />
              <Button onClick={() => { setSuccess(null); setForm({ name: user?.name || "", email: user?.email || "", phone: user?.phone || "", amount: "", pan_number: user?.pan_number || "", aadhaar_number: user?.aadhaar_number || "", address: user?.address || "", message: "" }); }} variant="outline" className="rounded-full px-8 py-3 mt-2" data-testid="donate-again-btn">
                {t.donate_again}
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
              <ArrowLeft className="w-4 h-4" /> {t.back_to_form}
            </button>
            <div className="w-14 h-14 rounded-full bg-[#1E56A0]/10 flex items-center justify-center mx-auto mb-4">
              <Mail className="w-7 h-7 text-[#1E56A0]" />
            </div>
            <h2 className="text-2xl font-semibold text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.verify_email}</h2>
            <p className="text-sm text-slate-500 mb-6">{t.otp_sent_to} <strong className="text-[#0D2847]">{form.email}</strong></p>
            {otpDebug && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4">
                <p className="text-xs text-amber-700">{t.debug_otp_notice}</p>
                <p className="text-2xl font-bold text-amber-800 tracking-[0.3em] mt-1" data-testid="donate-debug-otp">{otpDebug}</p>
              </div>
            )}
            <Input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="000000" maxLength={6}
              className="rounded-xl text-center text-2xl tracking-[0.3em] font-semibold mb-4" data-testid="donate-otp-input" />
            <Button onClick={handleVerifyOtp} disabled={submitting} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3" data-testid="donate-verify-otp-btn">
              {submitting ? t.verifying : t.verify_donate}
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
              <p className="text-sm text-green-800">{t.logged_in_as} <strong>{user.name}</strong>. {t.logged_in_notice}</p>
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

            {/* Cover Razorpay transaction fee — donor opts to top up so HHF nets the full pledge */}
            <label className={`flex items-start gap-3 rounded-xl border-2 p-3 cursor-pointer transition-all ${coverFee ? "border-emerald-500 bg-emerald-50" : "border-emerald-200 bg-emerald-50/30 hover:bg-emerald-50/60"}`} data-testid="cover-fee-section">
              <input type="checkbox" checked={coverFee} onChange={e => setCoverFee(e.target.checked)} className="mt-1 w-4 h-4 accent-emerald-600" data-testid="cover-fee-toggle" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-emerald-900">
                  {lang === "hi" ? "लेन-देन शुल्क मैं कवर करना चाहूंगा (Razorpay 2.36%)" : "Cover the Razorpay transaction fee (~2.36%)"}
                </p>
                <p className="text-[11px] text-emerald-800/80 mt-0.5">
                  {lang === "hi"
                    ? "यदि आप टॉगल करते हैं, तो Razorpay की 2% + GST फीस आप वहन करेंगे ताकि Heroic HIFI को आपकी पूरी प्रतिज्ञा मिले।"
                    : "Razorpay deducts ~2.36% from every donation. Toggle this on to absorb that fee yourself so Heroic HIFI Foundation receives your full pledge. Your 80G receipt still reflects only the pledged amount you donated."}
                </p>
                {coverFee && !recurring && form.amount && (
                  <p className="text-xs text-emerald-700 mt-2 font-medium" data-testid="onetime-fee-preview">
                    Pledge {"\u20B9"} {Number(form.amount).toLocaleString("en-IN")} + Fee {"\u20B9"} {oneTimeFee.toLocaleString("en-IN")} = <strong>You pay {"\u20B9"} {(Number(form.amount) + oneTimeFee).toLocaleString("en-IN")}</strong>
                  </p>
                )}
                {coverFee && recurring && customRecurring && (
                  <p className="text-xs text-emerald-700 mt-2 font-medium" data-testid="custom-sub-fee-preview">
                    Pledge {"\u20B9"} {Number(customSubAmount).toLocaleString("en-IN")} + Fee {"\u20B9"} {subFee.toLocaleString("en-IN")} per cycle = <strong>You're charged {"\u20B9"} {(Number(customSubAmount) + subFee).toLocaleString("en-IN")} every {customInterval.replace("_", " ")}</strong>
                  </p>
                )}
                {coverFee && recurring && !customRecurring && (
                  <p className="text-[11px] text-amber-700 mt-2">
                    Note: fee-cover currently applies to one-time donations and <em>custom</em> recurring amounts only — fixed plan amounts are pre-set in Razorpay.
                  </p>
                )}
              </div>
            </label>

            {/* Recurring Donation Toggle */}
            <div className={`rounded-xl border-2 p-4 transition-all ${recurring ? "border-[#FF7F00] bg-[#FF7F00]/5" : "border-sky-100 bg-white"}`} data-testid="recurring-toggle-section">
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" checked={recurring} onChange={e => setRecurring(e.target.checked)} className="mt-1 w-4 h-4 accent-[#FF7F00]" data-testid="recurring-toggle" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-[#0D2847]">{lang === "hi" ? "हर महीने स्वचालित दान बनाएं" : "Make this a recurring donation"}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {lang === "hi"
                      ? "Razorpay UPI AutoPay/कार्ड के माध्यम से स्वचालित दान। 6 बार सफल भुगतान के बाद 'Heroic Patron' टियर अनलॉक होता है।"
                      : "Automatic donations via Razorpay UPI AutoPay / cards. Hit 6 successful charges to unlock the 'Heroic Patron' tier on the Wall of Fame. Cancel anytime from your dashboard."}
                  </p>
                  {recurring && !user && (
                    <p className="text-xs text-amber-700 mt-2 font-medium">{lang === "hi" ? "कृपया पहले लॉग इन करें।" : "Please log in to set up a recurring donation."}</p>
                  )}
                  {recurring && user && (
                    <>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3" data-testid="recurring-plan-row">
                        {RECURRING_PLANS.map(p => {
                          const active = !customRecurring && recurringPlan === p.key;
                          return (
                            <button
                              key={p.key}
                              type="button"
                              onClick={() => { setCustomRecurring(false); setRecurringPlan(p.key); }}
                              data-testid={`plan-${p.key}`}
                              className={`p-3 rounded-xl border-2 text-center transition-all ${active ? "border-[#FF7F00] bg-[#FF7F00] text-white shadow-md" : "border-amber-200 bg-white text-slate-700 hover:border-amber-300"}`}
                            >
                              <p className={`text-xs font-semibold uppercase tracking-wider ${active ? "text-white/90" : "text-slate-500"}`}>{lang === "hi" ? p.hi : p.en}</p>
                              <p className={`text-lg font-bold mt-0.5 ${active ? "text-white" : "text-[#0D2847]"}`} style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                                {"\u20B9"}{p.amount.toLocaleString("en-IN")}
                              </p>
                              <p className={`text-[10px] mt-0.5 ${active ? "text-white/80" : "text-slate-400"}`}>{p.sub.split(" ").slice(1).join(" ")}</p>
                            </button>
                          );
                        })}
                      </div>
                      <button
                        type="button"
                        onClick={() => setCustomRecurring(c => !c)}
                        className={`mt-3 w-full text-xs px-3 py-2 rounded-xl border-2 transition-all ${customRecurring ? "border-[#FF7F00] bg-[#FF7F00]/5 text-[#FF7F00] font-semibold" : "border-dashed border-amber-300 text-amber-700 hover:bg-amber-50"}`}
                        data-testid="toggle-custom-recurring"
                      >
                        {customRecurring ? "\u2713 Using a custom recurring amount — click again to use a fixed plan" : "Or pick a custom amount & frequency \u2192"}
                      </button>
                      {customRecurring && (
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3 bg-amber-50/40 border border-amber-200 rounded-xl p-3" data-testid="custom-recurring-row">
                          <div className="sm:col-span-1">
                            <label className="text-[10px] font-medium text-amber-800 uppercase tracking-wider">Amount per cycle ({"\u20B9"})</label>
                            <input
                              type="number" min={100} step={50} value={customSubAmount}
                              onChange={e => setCustomSubAmount(e.target.value)}
                              className="w-full mt-1 px-3 py-2 rounded-lg border border-amber-200 text-sm font-semibold text-[#0D2847]"
                              data-testid="custom-amount-input"
                            />
                            <p className="text-[10px] text-amber-700/80 mt-1">Min {"\u20B9"} 100 / cycle.</p>
                          </div>
                          <div className="sm:col-span-2">
                            <label className="text-[10px] font-medium text-amber-800 uppercase tracking-wider">How often?</label>
                            <div className="grid grid-cols-4 gap-1 mt-1">
                              {[
                                { k: "monthly", l: "Monthly" },
                                { k: "quarterly", l: "Quarterly" },
                                { k: "half_yearly", l: "Half-yearly" },
                                { k: "annual", l: "Annual" },
                              ].map(it => (
                                <button
                                  key={it.k}
                                  type="button"
                                  onClick={() => setCustomInterval(it.k)}
                                  className={`text-[11px] px-2 py-2 rounded-lg border-2 transition-colors ${customInterval === it.k ? "border-[#FF7F00] bg-[#FF7F00] text-white font-semibold" : "border-amber-200 bg-white text-slate-700 hover:border-amber-300"}`}
                                  data-testid={`custom-interval-${it.k}`}
                                >{it.l}</button>
                              ))}
                            </div>
                            <p className="text-[10px] text-amber-700/80 mt-1.5">Razorpay auto-charges {"\u20B9"}{Number(customSubAmount || 0).toLocaleString("en-IN")} every {customInterval.replace("_", " ")} on your saved payment method.</p>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-slate-700">{t.pan} *</Label>
                <Input name="pan_number" value={form.pan_number} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-pan-input" placeholder="ABCDE1234F" required />
                <p className="text-xs text-slate-400 mt-1">{t.pan_help}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-slate-700">{t.aadhaar}</Label>
                <Input name="aadhaar_number" value={form.aadhaar_number} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-aadhaar-input" placeholder="1234 5678 9012" />
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium text-slate-700">{t.address}</Label>
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
              {submitting ? t.processing : user ? t.submit : t.verify_email_donate}
            </Button>
          </form>
        </div>
      </section>
    </div>
  );
}
