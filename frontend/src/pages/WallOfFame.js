import { useState, useEffect, useCallback } from "react";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import api from "../lib/api";
import { motion } from "framer-motion";
import { Award, Clock, IndianRupee, Star, Trophy, Crown, Repeat, Heart, Compass, Sparkles, Calendar, ShieldCheck } from "lucide-react";

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

const formatDate = (iso) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  } catch { return "—"; }
};

const tenureLabel = (start, end) => {
  if (!start) return "";
  const s = formatDate(start);
  if (!end) return `Since ${s}`;
  return `${s} → ${formatDate(end)}`;
};

function SectionHeader({ icon: Icon, accent, overline, title, subtitle }) {
  return (
    <div className="text-center mb-10">
      <div className={`inline-flex items-center gap-2 ${accent.bg} border ${accent.border} rounded-full px-4 py-1.5 mb-4`}>
        <Icon className={`w-3.5 h-3.5 ${accent.text}`} />
        <span className={`text-xs font-medium ${accent.text} uppercase tracking-widest`}>{overline}</span>
      </div>
      <h2 className="text-3xl sm:text-4xl font-semibold text-white mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{title}</h2>
      {subtitle && <p className="text-sm text-slate-400 max-w-xl mx-auto">{subtitle}</p>}
    </div>
  );
}

function LedgerCard({ entry, kind, index }) {
  const isActive = !entry.ended_at;
  const isTop = kind === "top";
  const accent = isTop
    ? { bg: "bg-amber-500/10", text: "text-amber-300", border: "border-amber-500/30", glow: "from-amber-500/20" }
    : { bg: "bg-rose-500/10", text: "text-rose-300", border: "border-rose-500/30", glow: "from-rose-500/20" };
  const Ic = isTop ? Trophy : Heart;
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.96 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.06, ease: "easeOut" }}
      className="group relative"
      data-testid={`${kind}-ledger-${entry.id}`}
    >
      <div className={`absolute -inset-0.5 bg-gradient-to-br ${accent.glow} via-transparent to-transparent rounded-2xl opacity-60 group-hover:opacity-100 transition-opacity blur`} />
      <div className={`relative bg-gradient-to-br from-[#0D2847] to-[#162D50] rounded-2xl border ${accent.border} overflow-hidden shadow-xl`}>
        {isActive && (
          <div className={`absolute top-3 right-3 inline-flex items-center gap-1 ${accent.bg} backdrop-blur ${accent.border} border rounded-full px-2.5 py-0.5`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isTop ? "bg-amber-400" : "bg-rose-400"} animate-pulse`} />
            <span className={`text-[9px] font-bold uppercase tracking-widest ${accent.text}`}>Holding</span>
          </div>
        )}
        <div className="h-1 bg-gradient-to-r from-[#FF7F00] via-amber-400 to-[#28A9E2]" />
        <div className="p-5">
          <div className="flex items-start gap-3 mb-3">
            <div className={`w-12 h-12 rounded-full ${accent.bg} flex items-center justify-center shrink-0 border ${accent.border}`}>
              <Ic className={`w-5 h-5 ${accent.text}`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className={`text-[10px] ${accent.text} font-medium uppercase tracking-widest`}>FY {entry.fy_label}</p>
              <h3 className="text-lg font-semibold text-white truncate" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{entry.donor_name}</h3>
            </div>
          </div>
          <div className={`${accent.bg} border ${accent.border} rounded-xl p-3 text-center mb-3`}>
            {isTop ? (
              <>
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Contribution (rounded)</p>
                <p className="text-2xl font-bold text-white">₹{Number(entry.peak_amount || 0).toLocaleString("en-IN")}</p>
              </>
            ) : (
              <>
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Fees Absorbed (rounded)</p>
                <p className="text-2xl font-bold text-white">₹{Number(entry.peak_fee || 0).toLocaleString("en-IN")}</p>
                <p className="text-[10px] text-slate-400 mt-1">on a pledge of ₹{Number(entry.peak_pledge || 0).toLocaleString("en-IN")}</p>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Calendar className="w-3 h-3" /> {tenureLabel(entry.awarded_at, entry.ended_at)}
          </p>
          {entry.ended_reason && (
            <p className="text-[10px] text-slate-500 mt-1 italic">{entry.ended_reason}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function OfficeCard({ entry, index }) {
  const isActive = !entry.end_date;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.45, delay: index * 0.05 }}
      className="bg-gradient-to-br from-[#0D2847] to-[#1a3460] rounded-xl border border-amber-500/20 p-4"
      data-testid={`office-tenure-${entry.id || index}`}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center shrink-0">
          <Compass className="w-4 h-4 text-amber-300" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-200 border border-amber-500/30 font-medium">{entry.post}</span>
            {isActive && <span className="text-[10px] inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />In office</span>}
          </div>
          <h3 className="text-base font-semibold text-white mt-1" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{entry.user_name || entry.user_email}</h3>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5">
            <Calendar className="w-3 h-3" /> {tenureLabel(entry.start_date, entry.end_date)}
          </p>
          {entry.leadership_bio && (
            <p className="text-[11px] text-slate-300/80 mt-2 leading-relaxed italic">&ldquo;{entry.leadership_bio}&rdquo;</p>
          )}
          {entry.end_reason && !isActive && (
            <p className="text-[10px] text-slate-500 mt-1.5 italic">{entry.end_reason}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function PatronCard({ patron, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.07 }}
      className="group relative"
      data-testid={`patron-card-${patron.email}`}
    >
      <div className="absolute -inset-0.5 bg-gradient-to-br from-fuchsia-500/30 via-amber-400/20 to-fuchsia-500/30 rounded-2xl opacity-60 group-hover:opacity-100 transition-opacity blur" />
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
                {patron.patron_plan === "monthly" ? "Monthly Sustainer" : patron.patron_plan === "annual" ? "Annual Sustainer" : "Quarterly Sustainer"}
              </p>
              {patron.patron_since && (
                <p className="text-[10px] text-slate-400 mt-0.5">Since {formatDate(patron.patron_since)}</p>
              )}
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

function BadgeHolderCard({ holder, badge, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.04 }}
      className="bg-gradient-to-br from-[#0D2847] to-[#162D50] rounded-xl border border-white/10 p-4 hover:border-white/20 transition-colors"
      data-testid={`badge-holder-${badge.replace(/\s+/g, "-").toLowerCase()}-${holder.email}`}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
          <span className="text-base font-bold text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {holder.name?.charAt(0)?.toUpperCase() || "?"}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-semibold text-white truncate">{holder.name}</h4>
          <span className={`inline-block mt-1 text-[9px] px-2 py-0.5 rounded-full border font-medium ${BADGE_COLORS[badge] || "bg-slate-800 text-slate-300 border-slate-700"}`}>
            {badge}
          </span>
          {holder.designation && (
            <p className="text-[10px] text-amber-300/80 mt-1.5 flex items-center gap-1"><Compass className="w-2.5 h-2.5" />{holder.designation}{holder.tenure_start && ` · since ${formatDate(holder.tenure_start)}`}</p>
          )}
          {holder.volunteer_hours > 0 && (
            <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1"><Clock className="w-2.5 h-2.5" />{holder.volunteer_hours} hrs</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function CuratedCard({ entry, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.55, delay: index * 0.07 }}
      className="group relative"
      data-testid={`curated-card-${entry.email}`}
    >
      <div className="absolute -inset-0.5 bg-gradient-to-br from-amber-400/20 via-transparent to-blue-400/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity blur-sm" />
      <div className="relative bg-gradient-to-br from-[#0D2847] to-[#162D50] rounded-2xl border border-white/10 overflow-hidden shadow-xl">
        <div className="h-1 bg-gradient-to-r from-[#FF7F00] via-amber-400 to-[#28A9E2]" />
        <div className="p-6">
          <div className="flex items-start gap-4 mb-5">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#FF7F00]/30 to-[#28A9E2]/30 flex items-center justify-center shrink-0 border-2 border-amber-400/30 shadow-lg shadow-amber-500/10">
              <span className="text-xl font-bold text-white/90" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {entry.name?.charAt(0)?.toUpperCase() || "?"}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-base font-semibold text-white truncate" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{entry.name}</h3>
              <p className="text-[10px] text-amber-300/70 font-medium uppercase tracking-widest mt-0.5">
                {entry.role === "admin" ? "Founding Member" : "Helping Hero"}
              </p>
            </div>
            <Trophy className="w-5 h-5 text-amber-400/60 shrink-0" />
          </div>
          <div className="grid grid-cols-2 gap-2 mb-4">
            <div className="bg-white/5 rounded-xl p-2.5 text-center border border-white/5">
              <Clock className="w-3.5 h-3.5 text-blue-300/70 mx-auto mb-1" />
              <p className="text-base font-bold text-white">{entry.volunteer_hours || 0}</p>
              <p className="text-[9px] text-slate-400 uppercase tracking-wider">Hours</p>
            </div>
            <div className="bg-white/5 rounded-xl p-2.5 text-center border border-white/5">
              <IndianRupee className="w-3.5 h-3.5 text-amber-300/70 mx-auto mb-1" />
              <p className="text-base font-bold text-white">{(entry.total_donated || 0).toLocaleString("en-IN")}</p>
              <p className="text-[9px] text-slate-400 uppercase tracking-wider">Donated</p>
            </div>
          </div>
          {entry.contribution_summary && (
            <p className="text-xs text-slate-300/80 leading-relaxed italic">&ldquo;{entry.contribution_summary}&rdquo;</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function WallOfFame() {
  const { lang } = useLang();
  const t = translations[lang].wall_of_fame || {};
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [compRes, patronRes] = await Promise.all([
        api.get("/wall-of-fame/comprehensive"),
        api.get("/heroic-patrons"),
      ]);
      setData({ ...compRes.data, patrons_full: patronRes.data });
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const topDonors = data?.top_donors || [];
  const generousDonors = data?.most_generous_donors || [];
  const officeBearers = data?.office_bearers || [];
  const patrons = data?.patrons_full || data?.heroic_patrons || [];
  const badgeHolders = data?.badge_holders || {};
  const curated = (data?.curated || []).filter((e) => e.tier !== "heroic_patron");

  const officeCurrent = officeBearers.filter((e) => !e.end_date);
  const officePast = officeBearers.filter((e) => e.end_date);

  // Flatten badge holders, but skip Top Donor / Most Generous (covered above)
  const flatHolders = [];
  Object.entries(badgeHolders).forEach(([badge, holders]) => {
    if (badge === "Top Donor" || badge === "Most Generous Donor") return;
    holders.forEach((h) => flatHolders.push({ ...h, _badge: badge }));
  });

  return (
    <div data-testid="wall-of-fame-page" className="bg-[#060E1A] min-h-screen">
      {/* Hero */}
      <section className="relative py-24 sm:py-32 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#1E56A0]/20 via-transparent to-transparent" />
        <div className="absolute top-20 left-10 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-full px-4 py-1.5 mb-6">
            <Star className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs font-medium text-amber-300 uppercase tracking-widest">{t.overline || "Honouring Our Heroes"}</span>
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-4"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.title || "Wall of Fame"}</motion.h1>
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
            {t.subtitle || "Celebrating the extraordinary individuals whose selfless contributions have shaped our mission and touched countless lives."}
          </motion.p>
          {data?.privacy_note && (
            <p className="text-[11px] text-amber-200/60 mt-6 inline-flex items-center gap-1.5"><ShieldCheck className="w-3 h-3" /> {data.privacy_note}</p>
          )}
        </div>
      </section>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {/* Top Donors of the Year (with tenure) */}
          {topDonors.length > 0 && (
            <section className="pb-12" data-testid="top-donors-section">
              <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <SectionHeader
                  icon={Trophy}
                  accent={{ bg: "bg-amber-500/10", text: "text-amber-300", border: "border-amber-500/30" }}
                  overline="Top Donor of the Year"
                  title={lang === "hi" ? "वर्ष के शीर्ष दानदाता" : "Top Donors — Through the Years"}
                  subtitle={lang === "hi" ? "हर वित्त वर्ष के सबसे बड़े योगदानकर्ता।" : "The largest single contributor in each financial year — an evergreen honour roll."}
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                  {topDonors.map((e, i) => <LedgerCard key={e.id} entry={e} kind="top" index={i} />)}
                </div>
              </div>
            </section>
          )}

          {/* Most Generous Donors */}
          {generousDonors.length > 0 && (
            <section className="pb-12" data-testid="most-generous-section">
              <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <SectionHeader
                  icon={Heart}
                  accent={{ bg: "bg-rose-500/10", text: "text-rose-300", border: "border-rose-500/30" }}
                  overline="Most Generous Donor of the Year"
                  title={lang === "hi" ? "सबसे उदार दानदाता" : "Most Generous Donors"}
                  subtitle={lang === "hi" ? "जिन्होंने सर्वाधिक प्रसंस्करण शुल्क अवशोषित किए।" : "Donors who voluntarily absorbed the most in payment-gateway fees so the foundation receives every rupee of their pledge."}
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                  {generousDonors.map((e, i) => <LedgerCard key={e.id} entry={e} kind="generous" index={i} />)}
                </div>
              </div>
            </section>
          )}

          {/* Heroic Patrons */}
          {patrons.length > 0 && (
            <section className="pb-12" data-testid="heroic-patrons-section">
              <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <SectionHeader
                  icon={Crown}
                  accent={{ bg: "bg-fuchsia-500/10", text: "text-fuchsia-200", border: "border-fuchsia-500/30" }}
                  overline="Recurring Sustainers"
                  title={lang === "hi" ? "हीरोइक संरक्षक" : "Our Heroic Patrons"}
                  subtitle={lang === "hi" ? "हर महीने हमारे मिशन को बल देने वाले प्रतिबद्ध दानदाता।" : "Committed sustainers whose recurring contributions power every mission, month after month."}
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                  {patrons.map((p, i) => <PatronCard key={p.email} patron={p} index={i} />)}
                </div>
              </div>
            </section>
          )}

          {/* Office Bearers — Current + Past */}
          {officeBearers.length > 0 && (
            <section className="pb-12" data-testid="office-bearers-section">
              <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <SectionHeader
                  icon={Compass}
                  accent={{ bg: "bg-amber-500/10", text: "text-amber-300", border: "border-amber-500/30" }}
                  overline="Governance"
                  title={lang === "hi" ? "कार्यालय धारक" : "Office Bearers"}
                  subtitle={lang === "hi" ? "वर्तमान एवं पूर्व — पूर्ण कार्यकाल इतिहास।" : "Current and past — full tenure history of every Chairman, Secretary, Treasurer, Event Incharge & Assistant."}
                />
                {officeCurrent.length > 0 && (
                  <>
                    <p className="text-[10px] text-emerald-300/80 uppercase tracking-widest text-center mb-4 flex items-center justify-center gap-1.5">
                      <span className="w-1 h-1 rounded-full bg-emerald-400" /> Currently in Office
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
                      {officeCurrent.map((e, i) => <OfficeCard key={e.id || i} entry={e} index={i} />)}
                    </div>
                  </>
                )}
                {officePast.length > 0 && (
                  <>
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest text-center mb-4">Past Tenures</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {officePast.map((e, i) => <OfficeCard key={e.id || i} entry={e} index={i} />)}
                    </div>
                  </>
                )}
              </div>
            </section>
          )}

          {/* Star Volunteers / Rising Stars / etc. */}
          {flatHolders.length > 0 && (
            <section className="pb-12" data-testid="badge-holders-section">
              <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <SectionHeader
                  icon={Sparkles}
                  accent={{ bg: "bg-cyan-500/10", text: "text-cyan-300", border: "border-cyan-500/30" }}
                  overline="Distinguished Heroes"
                  title={lang === "hi" ? "विशिष्ट हीरो" : "Star Volunteers, Builders & Rising Stars"}
                  subtitle={lang === "hi" ? "हमारे समर्पित स्वयंसेवक जिन्हें विशेष पहचान मिली है।" : "Volunteers and members recognised for sustained impact across our missions."}
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {flatHolders.map((h, i) => <BadgeHolderCard key={`${h._badge}-${h.email}`} holder={h} badge={h._badge} index={i} />)}
                </div>
              </div>
            </section>
          )}

          {/* Curated Helping Heroes */}
          {curated.length > 0 && (
            <section className="pb-24 sm:pb-32" data-testid="curated-section">
              <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <SectionHeader
                  icon={Award}
                  accent={{ bg: "bg-emerald-500/10", text: "text-emerald-300", border: "border-emerald-500/30" }}
                  overline="Helping Heroes"
                  title={lang === "hi" ? "उल्लेखनीय योगदानकर्ता" : "Notable Contributors"}
                  subtitle={lang === "hi" ? "व्यवस्थापक द्वारा चयनित सम्मानित सदस्य।" : "Hand-picked by our administrators for their lasting contributions to the foundation's journey."}
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                  {curated.map((e, i) => <CuratedCard key={e.email} entry={e} index={i} />)}
                </div>
              </div>
            </section>
          )}

          {/* Empty state */}
          {!loading && topDonors.length === 0 && generousDonors.length === 0 && patrons.length === 0 && officeBearers.length === 0 && flatHolders.length === 0 && curated.length === 0 && (
            <div className="text-center py-20 max-w-2xl mx-auto px-4">
              <Award className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500">{t.empty || "The Wall of Fame awaits its first heroes."}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
