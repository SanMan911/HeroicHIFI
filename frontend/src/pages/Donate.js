import { useState } from "react";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { Heart, ShieldCheck, IndianRupee } from "lucide-react";
import { toast } from "sonner";

const PRESET_AMOUNTS = [500, 1000, 2500, 5000, 10000, 25000];

export default function Donate() {
  const { lang } = useLang();
  const t = translations[lang].donate;
  const [form, setForm] = useState({ name: "", email: "", phone: "", amount: "", pan_number: "", message: "" });
  const [customAmount, setCustomAmount] = useState(false);
  const [submitting, setSubmitting] = useState(false);

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
      const { data } = await api.post("/donations", { ...form, amount: parseInt(form.amount, 10) });
      toast.success(data.message);
      setForm({ name: "", email: "", phone: "", amount: "", pan_number: "", message: "" });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div data-testid="donate-page">
      <section className="relative py-24 sm:py-32 bg-gradient-to-br from-[#1E56A0] to-[#28A9E2]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-6">
            <Heart className="w-8 h-8 text-white" />
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.title}
          </motion.h1>
          <p className="text-base sm:text-lg text-blue-100 max-w-2xl mx-auto">{t.subtitle}</p>
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-8 flex items-start gap-3" data-testid="razorpay-note">
            <ShieldCheck className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
            <p className="text-sm text-amber-800">{t.note}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" data-testid="donation-form">
            <div>
              <Label htmlFor="donate-name" className="text-sm font-medium text-stone-700">{t.name} *</Label>
              <Input id="donate-name" name="name" value={form.name} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-name-input" required />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="donate-email" className="text-sm font-medium text-stone-700">{t.email} *</Label>
                <Input id="donate-email" name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-email-input" required />
              </div>
              <div>
                <Label htmlFor="donate-phone" className="text-sm font-medium text-stone-700">{t.phone} *</Label>
                <Input id="donate-phone" name="phone" value={form.phone} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-phone-input" required />
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium text-stone-700 mb-3 block">{t.preset_amounts}</Label>
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 mb-3">
                {PRESET_AMOUNTS.map((amt) => (
                  <button
                    type="button"
                    key={amt}
                    onClick={() => selectAmount(amt)}
                    className={`py-3 px-4 rounded-xl text-sm font-medium border transition-all ${
                      form.amount === String(amt) && !customAmount
                        ? "bg-[#1E56A0] text-white border-[#1E56A0]"
                        : "bg-white text-stone-700 border-sky-100 hover:border-[#1E56A0]/30"
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
                    customAmount ? "bg-[#1E56A0] text-white border-[#1E56A0]" : "bg-white text-stone-700 border-sky-100 hover:border-[#1E56A0]/30"
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
              <Label htmlFor="donate-pan" className="text-sm font-medium text-stone-700">{t.pan}</Label>
              <Input id="donate-pan" name="pan_number" value={form.pan_number} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="donate-pan-input" placeholder="ABCDE1234F" />
              <p className="text-xs text-stone-400 mt-1">{t.pan_help}</p>
            </div>

            <div>
              <Label htmlFor="donate-message" className="text-sm font-medium text-stone-700">{t.message}</Label>
              <Textarea id="donate-message" name="message" value={form.message} onChange={handleChange} rows={3} className="mt-1.5 rounded-xl" data-testid="donate-message-input" />
            </div>

            <Button
              type="submit"
              disabled={submitting}
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
