import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { ORG_INFO, MEDIA } from "../data/missions";
import { motion } from "framer-motion";
import { Building2, Mail, Phone, MapPin, Eye, Compass, User, CalendarClock } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../lib/api";

export default function About() {
  const { lang } = useLang();
  const t = translations[lang].about;
  const [leaders, setLeaders] = useState([]);

  useEffect(() => {
    (async () => {
      try { const { data } = await api.get("/leadership"); setLeaders(data || []); }
      catch { setLeaders([]); }
    })();
  }, []);

  return (
    <div data-testid="about-page">
      {/* Hero */}
      <section className="relative py-24 sm:py-32 bg-[#1E56A0]">
        <div className="absolute inset-0 opacity-10">
          <img src={MEDIA.volunteers} alt="" className="w-full h-full object-cover" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-[#FF7F00] mb-4">
            {t.overline}
          </motion.p>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.title}
          </motion.h1>
        </div>
      </section>

      {/* Story */}
      <section className="py-20 sm:py-28">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="space-y-6">
            <p className="text-base sm:text-lg text-stone-600 leading-relaxed">{t.story_p1}</p>
            <p className="text-base sm:text-lg text-stone-600 leading-relaxed">{t.story_p2}</p>
            <p className="text-base sm:text-lg text-stone-600 leading-relaxed">{t.story_p3}</p>
          </motion.div>
        </div>
      </section>

      {/* Vision */}
      <section className="py-20 bg-gradient-to-r from-[#C8F2CE]/30 via-[#A7D9E8]/30 to-[#91C8E7]/30" data-testid="vision-section">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center mx-auto mb-6">
            <Eye className="w-8 h-8 text-[#1E56A0]" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-medium tracking-tight text-[#0D2847] mb-6" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.vision_title}
          </h2>
          <p className="text-base sm:text-lg text-stone-600 leading-relaxed max-w-3xl mx-auto">{t.vision_text}</p>
        </div>
      </section>

      {/* Leadership / Mission Stewards */}
      {leaders.length > 0 && (
        <section className="py-20 sm:py-24" data-testid="leadership-section">
          <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-50 border border-amber-200 text-xs font-medium text-amber-800 uppercase tracking-[0.18em] mb-4">
                <Compass className="w-3.5 h-3.5" /> Mission Stewards
              </div>
              <h2 className="text-3xl sm:text-4xl font-medium tracking-tight text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                The hands behind the mission
              </h2>
              <p className="text-sm text-stone-500 mt-3 max-w-2xl mx-auto">Office bearers and trustees you can reach out to. They volunteer their time exactly like every other hero in our foundation — the only difference is they also hold the paperwork.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="leadership-grid">
              {leaders.map(l => (
                <article key={l.email} className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6 hover:shadow-md transition-shadow flex flex-col" data-testid={`leader-card-${l.email}`}>
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-100 to-amber-50 border border-amber-200 flex items-center justify-center overflow-hidden shrink-0">
                      {l.profile_pic_path
                        ? <img src={`${process.env.REACT_APP_BACKEND_URL}${l.profile_pic_path}`} alt={l.name} className="w-full h-full object-cover" />
                        : <User className="w-6 h-6 text-amber-700" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-semibold text-[#0D2847] truncate">{l.name}</p>
                      {l.designation && <p className="text-xs font-medium text-amber-800 mt-0.5">{l.designation}</p>}
                      {l.bio && <p className="text-sm text-stone-600 mt-2 leading-relaxed">{l.bio}</p>}
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-amber-100/70 flex items-center justify-between gap-2">
                    <a href={`mailto:${l.email}`} className="inline-flex items-center gap-1 text-xs text-[#1E56A0] hover:underline truncate" data-testid={`leader-email-${l.email}`}>
                      <Mail className="w-3 h-3 shrink-0" /> <span className="truncate">{l.email}</span>
                    </a>
                    <a
                      href={`mailto:${l.email}?subject=${encodeURIComponent(`Meeting request with ${l.designation || "Mission Steward"} — Heroic HIFI Foundation`)}&body=${encodeURIComponent(`Hello ${l.name},\n\nI came across your profile on the Heroic HIFI Foundation website and would like to schedule a short 1:1 conversation regarding:\n\n[Please mention partnership, volunteering, mission queries, etc.]\n\nA few time slots that work for me:\n- \n- \n\nThank you,\n`)}`}
                      className="shrink-0 inline-flex items-center gap-1 text-[11px] font-medium px-3 py-1.5 rounded-full bg-amber-600 text-white hover:bg-amber-700 transition-colors"
                      data-testid={`leader-schedule-${l.email}`}
                    >
                      <CalendarClock className="w-3 h-3" /> Schedule 1:1
                    </a>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Legal Info */}
      <section className="py-20 sm:py-28" data-testid="legal-section">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <h2 className="text-3xl sm:text-4xl font-medium tracking-tight text-[#0D2847] mb-10 text-center" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.legal_title}
          </h2>
          <div className="bg-white rounded-2xl p-8 sm:p-10 shadow-sm border border-sky-100 space-y-6">
            <div className="flex items-start gap-4">
              <Building2 className="w-5 h-5 text-[#1E56A0] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.cin}</p>
                <p className="text-base font-semibold text-[#0D2847] font-mono">{ORG_INFO.cin}</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <MapPin className="w-5 h-5 text-[#1E56A0] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.registered_address}</p>
                <p className="text-base text-[#0D2847]">{ORG_INFO.address}</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Mail className="w-5 h-5 text-[#1E56A0] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.email}</p>
                <a href={`mailto:${ORG_INFO.email}`} className="text-base text-[#1E56A0] hover:underline">{ORG_INFO.email}</a>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Phone className="w-5 h-5 text-[#1E56A0] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.phone}</p>
                <a href={`tel:${ORG_INFO.phone}`} className="text-base text-[#1E56A0] hover:underline">{ORG_INFO.phone}</a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
