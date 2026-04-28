import { useState, useEffect, useCallback } from "react";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import api from "../lib/api";
import { motion } from "framer-motion";
import { Award, Clock, IndianRupee, Star, Trophy, Crown, Repeat } from "lucide-react";

const BADGE_COLORS = {
  "Helping Hero": "bg-green-900/40 text-green-300 border-green-700/50",
  "Heroic Patron": "bg-fuchsia-900/40 text-fuchsia-300 border-fuchsia-700/60",
  "Century Hero": "bg-yellow-900/40 text-yellow-300 border-yellow-700/50",
  "Generous Soul": "bg-amber-900/40 text-amber-300 border-amber-700/50",
  "Community Builder": "bg-blue-900/40 text-blue-300 border-blue-700/50",
  "Star Volunteer of the Month": "bg-pink-900/40 text-pink-300 border-pink-700/50",
  "Star Volunteer of the Quarter": "bg-purple-900/40 text-purple-300 border-purple-700/50",
  "Star Volunteer of the Year": "bg-red-900/40 text-red-300 border-red-700/50",
  "Top Donor": "bg-orange-900/40 text-orange-300 border-orange-700/50",
  "Most Generous Donor": "bg-rose-900/40 text-rose-300 border-rose-700/60",
  "Rising Star": "bg-cyan-900/40 text-cyan-300 border-cyan-700/50",
};

function FameCard({ entry, index }) {
  const delay = index * 0.1;
  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.95 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      className="group relative"
      data-testid={`fame-card-${entry.email}`}
    >
      {/* Glow effect */}
      <div className="absolute -inset-0.5 bg-gradient-to-br from-amber-400/20 via-transparent to-blue-400/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm" />

      <div className="relative bg-gradient-to-br from-[#0D2847] to-[#162D50] rounded-2xl border border-white/10 overflow-hidden shadow-xl hover:shadow-2xl hover:shadow-amber-500/5 transition-all duration-500 hover:-translate-y-1">
        {/* Top accent bar */}
        <div className="h-1 bg-gradient-to-r from-[#FF7F00] via-amber-400 to-[#28A9E2]" />

        <div className="p-6">
          {/* Avatar + Info */}
          <div className="flex items-start gap-4 mb-5">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#FF7F00]/30 to-[#28A9E2]/30 flex items-center justify-center shrink-0 border-2 border-amber-400/30 shadow-lg shadow-amber-500/10">
              <span className="text-2xl font-bold text-white/90" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {entry.name?.charAt(0)?.toUpperCase() || "?"}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-semibold text-white tracking-tight truncate" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {entry.name}
              </h3>
              <p className="text-xs text-amber-300/70 font-medium uppercase tracking-widest mt-0.5">
                {entry.role === "admin" ? "Founding Member" : "Helping Hero"}
              </p>
            </div>
            <Trophy className="w-5 h-5 text-amber-400/60 shrink-0 mt-1" />
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="bg-white/5 rounded-xl p-3 text-center border border-white/5">
              <Clock className="w-4 h-4 text-blue-300/70 mx-auto mb-1" />
              <p className="text-xl font-bold text-white">{entry.volunteer_hours || 0}</p>
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Hours</p>
            </div>
            <div className="bg-white/5 rounded-xl p-3 text-center border border-white/5">
              <IndianRupee className="w-4 h-4 text-amber-300/70 mx-auto mb-1" />
              <p className="text-xl font-bold text-white">{(entry.total_donated || 0).toLocaleString("en-IN")}</p>
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Donated</p>
            </div>
          </div>

          {/* Contribution Summary */}
          {entry.contribution_summary && (
            <p className="text-sm text-slate-300/80 leading-relaxed mb-4 italic">
              &ldquo;{entry.contribution_summary}&rdquo;
            </p>
          )}

          {/* Badges */}
          {(entry.badges || []).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {entry.badges.map((b) => (
                <span key={b} className={`text-[9px] px-2 py-0.5 rounded-full border font-medium ${BADGE_COLORS[b] || "bg-slate-800 text-slate-300 border-slate-700"}`}>
                  {b}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function PatronCard({ patron, index }) {
  const delay = index * 0.08;
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className="group relative"
      data-testid={`patron-card-${patron.email}`}
    >
      <div className="absolute -inset-0.5 bg-gradient-to-br from-fuchsia-500/30 via-amber-400/20 to-fuchsia-500/30 rounded-2xl opacity-60 group-hover:opacity-100 transition-opacity duration-500 blur" />
      <div className="relative bg-gradient-to-br from-[#1a0d2e] via-[#2a0f3a] to-[#0D2847] rounded-2xl border border-fuchsia-500/30 overflow-hidden shadow-xl">
        <div className="absolute top-3 right-3 flex items-center gap-1 bg-fuchsia-500/20 backdrop-blur border border-fuchsia-400/40 rounded-full px-2.5 py-1">
          <Crown className="w-3 h-3 text-fuchsia-300" />
          <span className="text-[9px] font-bold uppercase tracking-widest text-fuchsia-200">Heroic Patron</span>
        </div>
        <div className="h-1 bg-gradient-to-r from-fuchsia-500 via-amber-400 to-fuchsia-500" />
        <div className="p-5">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-fuchsia-500/40 to-amber-400/30 flex items-center justify-center shrink-0 border-2 border-fuchsia-300/40">
              <span className="text-xl font-bold text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {patron.name?.charAt(0)?.toUpperCase() || "?"}
              </span>
            </div>
            <div className="min-w-0 flex-1 mt-1">
              <h3 className="text-base font-semibold text-white truncate" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{patron.name}</h3>
              <p className="text-[10px] text-fuchsia-300/80 font-medium uppercase tracking-widest mt-0.5">
                {patron.patron_plan === "monthly" ? "Monthly Sustainer" : "Quarterly Sustainer"}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="bg-fuchsia-500/10 rounded-xl p-2.5 text-center border border-fuchsia-500/20">
              <Repeat className="w-3.5 h-3.5 text-fuchsia-300 mx-auto mb-1" />
              <p className="text-lg font-bold text-white" data-testid={`patron-charges-${patron.email}`}>{patron.patron_charge_count || 0}</p>
              <p className="text-[9px] text-slate-400 uppercase tracking-wider">Contributions</p>
            </div>
            <div className="bg-amber-500/10 rounded-xl p-2.5 text-center border border-amber-500/20">
              <IndianRupee className="w-3.5 h-3.5 text-amber-300 mx-auto mb-1" />
              <p className="text-lg font-bold text-white">{(patron.patron_total_amount || 0).toLocaleString("en-IN")}</p>
              <p className="text-[9px] text-slate-400 uppercase tracking-wider">Total Given</p>
            </div>
          </div>
          {patron.contribution_summary && (
            <p className="text-xs text-fuchsia-100/70 leading-relaxed italic">&ldquo;{patron.contribution_summary}&rdquo;</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function WallOfFame() {
  const { lang } = useLang();
  const t = translations[lang].wall_of_fame || {};
  const [entries, setEntries] = useState([]);
  const [patrons, setPatrons] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEntries = useCallback(async () => {
    try {
      const [wofRes, patronRes] = await Promise.all([
        api.get("/wall-of-fame"),
        api.get("/heroic-patrons"),
      ]);
      // Avoid duplication: patrons live in their own section above
      setEntries(wofRes.data.filter(e => e.tier !== "heroic_patron"));
      setPatrons(patronRes.data);
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchEntries(); }, [fetchEntries]);

  return (
    <div data-testid="wall-of-fame-page" className="bg-[#060E1A] min-h-screen">
      {/* Hero */}
      <section className="relative py-24 sm:py-32 overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#1E56A0]/20 via-transparent to-transparent" />
        <div className="absolute top-20 left-10 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl" />

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-full px-4 py-1.5 mb-6">
            <Star className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs font-medium text-amber-300 uppercase tracking-widest">
              {t.overline || "Honouring Our Heroes"}
            </span>
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.title || "Wall of Fame"}
          </motion.h1>

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto"
          >
            {t.subtitle || "Celebrating the extraordinary individuals whose selfless contributions have shaped our mission and touched countless lives."}
          </motion.p>
        </div>
      </section>

      {/* Heroic Patrons Section */}
      {!loading && patrons.length > 0 && (
        <section className="pb-12" data-testid="heroic-patrons-section">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-10">
              <div className="inline-flex items-center gap-2 bg-fuchsia-500/10 border border-fuchsia-400/30 rounded-full px-4 py-1.5 mb-4">
                <Crown className="w-3.5 h-3.5 text-fuchsia-300" />
                <span className="text-xs font-medium text-fuchsia-200 uppercase tracking-widest">Recurring Sustainers</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-semibold text-white mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {lang === "hi" ? "हीरोइक संरक्षक" : "Our Heroic Patrons"}
              </h2>
              <p className="text-sm text-slate-400 max-w-xl mx-auto">
                {lang === "hi"
                  ? "हर महीने हमारे मिशन को बल देने वाले प्रतिबद्ध दानदाता।"
                  : "Committed sustainers whose recurring contributions power every mission, month after month."}
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {patrons.map((p, i) => <PatronCard key={p.email} patron={p} index={i} />)}
            </div>
          </div>
        </section>
      )}

      {/* Grid */}
      <section className="pb-24 sm:pb-32">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-20">
              <Award className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500">{t.empty || "The Wall of Fame awaits its first heroes."}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {entries.map((entry, i) => (
                <FameCard key={entry.email} entry={entry} index={i} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
