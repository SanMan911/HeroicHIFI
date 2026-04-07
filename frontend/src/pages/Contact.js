import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { MISSIONS_CLIENT, ORG_INFO } from "../data/missions";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { motion } from "framer-motion";
import { MessageSquare, Mail, Phone, MapPin } from "lucide-react";
import { toast } from "sonner";

export default function Contact() {
  const { lang } = useLang();
  const t = translations[lang].contact;
  const [searchParams] = useSearchParams();
  const initialMission = searchParams.get("mission") || "";

  const [form, setForm] = useState({ name: "", email: "", mission: initialMission, subject: "", message: "" });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.subject || !form.message) {
      toast.error(lang === "hi" ? "कृपया सभी आवश्यक फ़ील्ड भरें" : "Please fill all required fields");
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await api.post("/queries", { ...form, mission: form.mission || "general" });
      toast.success(data.message);
      setForm({ name: "", email: "", mission: "", subject: "", message: "" });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div data-testid="contact-page">
      <section className="relative py-24 sm:py-32 bg-[#0D2847]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-6">
            <MessageSquare className="w-8 h-8 text-white" />
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.title}
          </motion.h1>
          <p className="text-base sm:text-lg text-stone-400 max-w-2xl mx-auto">{t.subtitle}</p>
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-12">
            <div className="lg:col-span-3">
              <form onSubmit={handleSubmit} className="space-y-6" data-testid="contact-form">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="contact-name" className="text-sm font-medium text-stone-700">{t.name} *</Label>
                    <Input id="contact-name" name="name" value={form.name} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="contact-name-input" required />
                  </div>
                  <div>
                    <Label htmlFor="contact-email" className="text-sm font-medium text-stone-700">{t.email} *</Label>
                    <Input id="contact-email" name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="contact-email-input" required />
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium text-stone-700 mb-1.5 block">{t.mission}</Label>
                  <Select value={form.mission} onValueChange={(val) => setForm({ ...form, mission: val })}>
                    <SelectTrigger className="rounded-xl" data-testid="contact-mission-select">
                      <SelectValue placeholder={t.mission_placeholder} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general" data-testid="contact-mission-general">{t.general}</SelectItem>
                      {MISSIONS_CLIENT.map((m) => (
                        <SelectItem key={m.slug} value={m.slug} data-testid={`contact-mission-${m.slug}`}>
                          {lang === "hi" ? m.name_hi : m.name}
                        </SelectItem>
                      ))}
                      <SelectItem value="blood-donation">{lang === "hi" ? "रक्तदान अभियान" : "Blood Donation Drives"}</SelectItem>
                      <SelectItem value="langar">{lang === "hi" ? "सामुदायिक भोजन (लंगर)" : "Community Kitchen (Langar)"}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="contact-subject" className="text-sm font-medium text-stone-700">{t.subject} *</Label>
                  <Input id="contact-subject" name="subject" value={form.subject} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="contact-subject-input" required />
                </div>

                <div>
                  <Label htmlFor="contact-message" className="text-sm font-medium text-stone-700">{t.message} *</Label>
                  <Textarea id="contact-message" name="message" value={form.message} onChange={handleChange} rows={5} className="mt-1.5 rounded-xl" data-testid="contact-message-input" required />
                </div>

                <Button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-[#0D2847] hover:bg-[#0D2847]/90 text-white rounded-full py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
                  data-testid="contact-submit-btn"
                >
                  {submitting ? (lang === "hi" ? "भेज रहे हैं..." : "Sending...") : t.submit}
                </Button>
              </form>
            </div>

            <div className="lg:col-span-2">
              <div className="bg-white rounded-2xl p-8 border border-sky-100 shadow-sm sticky top-28">
                <h3 className="text-xl font-medium text-[#0D2847] mb-6" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                  {t.info_title}
                </h3>
                <div className="space-y-5">
                  <a href={`mailto:${ORG_INFO.email}`} className="flex items-center gap-3 text-sm text-stone-600 hover:text-[#1E56A0] transition-colors">
                    <div className="w-10 h-10 rounded-xl bg-[#1E56A0]/5 flex items-center justify-center shrink-0">
                      <Mail className="w-4 h-4 text-[#1E56A0]" />
                    </div>
                    {ORG_INFO.email}
                  </a>
                  <a href={`tel:${ORG_INFO.phone}`} className="flex items-center gap-3 text-sm text-stone-600 hover:text-[#1E56A0] transition-colors">
                    <div className="w-10 h-10 rounded-xl bg-[#1E56A0]/5 flex items-center justify-center shrink-0">
                      <Phone className="w-4 h-4 text-[#1E56A0]" />
                    </div>
                    {ORG_INFO.phone}
                  </a>
                  <div className="flex items-start gap-3 text-sm text-stone-600">
                    <div className="w-10 h-10 rounded-xl bg-[#1E56A0]/5 flex items-center justify-center shrink-0 mt-0.5">
                      <MapPin className="w-4 h-4 text-[#1E56A0]" />
                    </div>
                    {ORG_INFO.address}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
