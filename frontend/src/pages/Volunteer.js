import { useState } from "react";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { MISSIONS_CLIENT } from "../data/missions";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { MEDIA } from "../data/missions";
import { motion } from "framer-motion";
import { Users } from "lucide-react";
import { toast } from "sonner";

export default function Volunteer() {
  const { lang } = useLang();
  const t = translations[lang].volunteer;
  const [form, setForm] = useState({ name: "", email: "", phone: "", city: "", interests: [], message: "" });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const toggleInterest = (slug) => {
    setForm((prev) => ({
      ...prev,
      interests: prev.interests.includes(slug)
        ? prev.interests.filter((s) => s !== slug)
        : [...prev.interests, slug],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.phone || !form.city) {
      toast.error(lang === "hi" ? "कृपया सभी आवश्यक फ़ील्ड भरें" : "Please fill all required fields");
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await api.post("/volunteers", form);
      toast.success(data.message);
      setForm({ name: "", email: "", phone: "", city: "", interests: [], message: "" });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div data-testid="volunteer-page">
      <section className="relative py-24 sm:py-32 overflow-hidden">
        <div className="absolute inset-0">
          <img src={MEDIA.volunteers} alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#1E56A0]/85 via-[#1E56A0]/70 to-[#1E56A0]/85" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-6">
            <Users className="w-8 h-8 text-white" />
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
          <form onSubmit={handleSubmit} className="space-y-6" data-testid="volunteer-form">
            <div>
              <Label htmlFor="vol-name" className="text-sm font-medium text-stone-700">{t.name} *</Label>
              <Input id="vol-name" name="name" value={form.name} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="volunteer-name-input" required />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="vol-email" className="text-sm font-medium text-stone-700">{t.email} *</Label>
                <Input id="vol-email" name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="volunteer-email-input" required />
              </div>
              <div>
                <Label htmlFor="vol-phone" className="text-sm font-medium text-stone-700">{t.phone} *</Label>
                <Input id="vol-phone" name="phone" value={form.phone} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="volunteer-phone-input" required />
              </div>
            </div>
            <div>
              <Label htmlFor="vol-city" className="text-sm font-medium text-stone-700">{t.city} *</Label>
              <Input id="vol-city" name="city" value={form.city} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="volunteer-city-input" required />
            </div>

            <div>
              <Label className="text-sm font-medium text-stone-700 mb-3 block">{t.interests}</Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {MISSIONS_CLIENT.map((m) => (
                  <label key={m.slug} className="flex items-center gap-3 p-3 rounded-xl border border-sky-100 hover:bg-stone-50 cursor-pointer transition-colors" data-testid={`volunteer-interest-${m.slug}`}>
                    <Checkbox
                      checked={form.interests.includes(m.slug)}
                      onCheckedChange={() => toggleInterest(m.slug)}
                    />
                    <span className="text-sm text-stone-700">{lang === "hi" ? m.name_hi : m.name}</span>
                  </label>
                ))}
                <label className="flex items-center gap-3 p-3 rounded-xl border border-sky-100 hover:bg-stone-50 cursor-pointer transition-colors" data-testid="volunteer-interest-blood">
                  <Checkbox checked={form.interests.includes("blood-donation")} onCheckedChange={() => toggleInterest("blood-donation")} />
                  <span className="text-sm text-stone-700">{lang === "hi" ? "रक्तदान अभियान" : "Blood Donation Drives"}</span>
                </label>
                <label className="flex items-center gap-3 p-3 rounded-xl border border-sky-100 hover:bg-stone-50 cursor-pointer transition-colors" data-testid="volunteer-interest-langar">
                  <Checkbox checked={form.interests.includes("langar")} onCheckedChange={() => toggleInterest("langar")} />
                  <span className="text-sm text-stone-700">{lang === "hi" ? "सामुदायिक भोजन (लंगर)" : "Community Kitchen (Langar)"}</span>
                </label>
              </div>
            </div>

            <div>
              <Label htmlFor="vol-message" className="text-sm font-medium text-stone-700">{t.message}</Label>
              <Textarea id="vol-message" name="message" value={form.message} onChange={handleChange} rows={3} className="mt-1.5 rounded-xl" data-testid="volunteer-message-input" />
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#1E56A0] hover:bg-[#1E56A0]/90 text-white rounded-full py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
              data-testid="volunteer-submit-btn"
            >
              {submitting ? (lang === "hi" ? "कृपया प्रतीक्षा करें..." : "Submitting...") : t.submit}
            </Button>
          </form>
        </div>
      </section>
    </div>
  );
}
