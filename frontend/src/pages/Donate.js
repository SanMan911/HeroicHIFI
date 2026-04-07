import { useState, useEffect } from "react";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { Heart, ShieldCheck, IndianRupee, CheckCircle } from "lucide-react";
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
  const t = translations[lang].donate;
  const [form, setForm] = useState({ name: "", email: "", phone: "", amount: "", pan_number: "", message: "" });
  const [customAmount, setCustomAmount] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const selectAmount = (amt) => { setForm({ ...form, amount: String(amt) }); setCustomAmount(false); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.phone || !form.amount) {
      toast.error(lang === "hi" ? "कृपया सभी आवश्यक फ़ील्ड भरें" : "Please fill all required fields");
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await api.post("/donations/create-order", { ...form, amount: parseInt(form.amount, 10) });
      if (data.razorpay_order_id) {
        const loaded = await loadRazorpayScript();
        if (!loaded) { toast.error("Failed to load payment gateway. Please try again."); setSubmitting(false); return; }
        const options = {
          key: data.razorpay_key,
          amount: data.amount,
          currency: data.currency,
          name: "Heroic HIFI Foundation",
          description: "Donation to Heroic HIFI Foundation",
          order_id: data.razorpay_order_id,
          handler: async function (response) {
            try {
              await api.post("/donations/verify-payment", {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                donation_id: data.donation.id,
              });
              toast.success(lang === "hi" ? "दान सफल! आपका हृदय से धन्यवाद।" : "Donation successful! Thank you for your generosity.");
              setSuccess(true);
              setForm({ name: "", email: "", phone: "", amount: "", pan_number: "", message: "" });
            } catch (err) {
              toast.error(lang === "hi" ? "भुगतान सत्यापन विफल" : "Payment verification failed. Please contact us.");
            }
            setSubmitting(false);
          },
          prefill: { name: form.name, email: form.email, contact: form.phone },
          theme: { color: "#1E56A0" },
          modal: { ondismiss: () => setSubmitting(false) },
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
      } else {
        toast.success(data.message || "Donation recorded. Our team will contact you.");
        setSuccess(true);
        setForm({ name: "", email: "", phone: "", amount: "", pan_number: "", message: "" });
        setSubmitting(false);
      }
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
      setSubmitting(false);
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
            <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}
            >
              {t.title}
            </motion.h1>
          </div>
        </section>
        <section className="py-20 sm:py-28">
          <div className="max-w-lg mx-auto px-4 sm:px-6 text-center">
            <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4 }}>
              <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-semibold text-[#0D2847] mb-3" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {lang === "hi" ? "आपका हृदय से धन्यवाद!" : "Thank You for Your Generosity!"}
              </h2>
              <p className="text-slate-500 mb-8">{lang === "hi" ? "आपका दान दर्ज हो गया है। हम शीघ्र ही आपसे सम्पर्क करेंगे।" : "Your donation has been recorded. We will reach out to you shortly."}</p>
              <Button onClick={() => setSuccess(false)} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full px-8 py-3" data-testid="donate-again-btn">
                {lang === "hi" ? "पुनः दान करें" : "Donate Again"}
              </Button>
            </motion.div>
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
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.title}
          </motion.h1>
          <p className="text-base sm:text-lg text-blue-100 max-w-2xl mx-auto">{t.subtitle}</p>
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 mb-8 flex items-start gap-3" data-testid="razorpay-note">
            <ShieldCheck className="w-5 h-5 text-[#1E56A0] mt-0.5 shrink-0" />
            <p className="text-sm text-[#0D2847]">{t.note}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" data-testid="donation-form">
            <div>
              <Label htmlFor="donate-name" className="text-sm font-medium text-slate-700">{t.name} *</Label>
              <Input id="donate-name" name="name" value={form.name} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-name-input" required />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="donate-email" className="text-sm font-medium text-slate-700">{t.email} *</Label>
                <Input id="donate-email" name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-email-input" required />
              </div>
              <div>
                <Label htmlFor="donate-phone" className="text-sm font-medium text-slate-700">{t.phone} *</Label>
                <Input id="donate-phone" name="phone" value={form.phone} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-phone-input" required />
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium text-slate-700 mb-3 block">{t.preset_amounts}</Label>
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 mb-3">
                {PRESET_AMOUNTS.map((amt) => (
                  <button
                    type="button" key={amt} onClick={() => selectAmount(amt)}
                    className={`py-3 px-4 rounded-xl text-sm font-medium border transition-all ${
                      form.amount === String(amt) && !customAmount
                        ? "bg-[#1E56A0] text-white border-[#1E56A0]"
                        : "bg-white text-slate-700 border-sky-100 hover:border-[#1E56A0]/30"
                    }`}
                    data-testid={`donate-amount-${amt}`}
                  >
                    <IndianRupee className="w-3 h-3 inline -mt-0.5" />{amt.toLocaleString("en-IN")}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => { setCustomAmount(true); setForm({ ...form, amount: "" }); }}
                  className={`py-3 px-4 rounded-xl text-sm font-medium border transition-all ${
                    customAmount ? "bg-[#1E56A0] text-white border-[#1E56A0]" : "bg-white text-slate-700 border-sky-100 hover:border-[#1E56A0]/30"
                  }`}
                  data-testid="donate-custom-amount-btn"
                >
                  {t.custom}
                </button>
              </div>
              {customAmount && (
                <Input name="amount" type="number" placeholder={t.amount} value={form.amount} onChange={handleChange} className="rounded-xl" data-testid="donate-custom-amount-input" />
              )}
            </div>

            <div>
              <Label htmlFor="donate-pan" className="text-sm font-medium text-slate-700">{t.pan}</Label>
              <Input id="donate-pan" name="pan_number" value={form.pan_number} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-pan-input" placeholder="ABCDE1234F" />
              <p className="text-xs text-slate-400 mt-1">{t.pan_help}</p>
            </div>

            <div>
              <Label htmlFor="donate-message" className="text-sm font-medium text-slate-700">{t.message}</Label>
              <Textarea id="donate-message" name="message" value={form.message} onChange={handleChange} rows={3} className="mt-1.5 rounded-xl" data-testid="donate-message-input" />
            </div>

            <Button
              type="submit" disabled={submitting}
              className="w-full bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
              data-testid="donate-submit-btn"
            >
              {submitting ? (lang === "hi" ? "कृपया प्रतीक्षा करें..." : "Processing...") : t.submit}
            </Button>
          </form>
        </div>
      </section>
    </div>
  );
}
