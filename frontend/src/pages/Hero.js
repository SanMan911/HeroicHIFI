import { useState, useEffect, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { motion } from "framer-motion";
import {
  Trophy, Heart, Crown, Star, Award, Compass, Calendar, Clock,
  IndianRupee, Share2, Check, Sparkles, ArrowLeft, ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";

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

const fmtDate = (iso) => {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); }
  catch { return "—"; }
};

const tenureLabel = (start, end) => {
  if (!start) return "";
  return end ? `${fmtDate(start)} → ${fmtDate(end)}` : `Since ${fmtDate(start)}`;
};

function StatTile({ icon: Ic, label, value, sub, accent = "amber" }) {
  const tone = {
    amber: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-300" },
    rose: { bg: "bg-rose-500/10", border: "border-rose-500/30", text: "text-rose-300" },
    blue: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-300" },
    fuchsia: { bg: "bg-fuchsia-500/10", border: "border-fuchsia-500/30", text: "text-fuchsia-300" },
  }[accent] || { bg: "bg-white/5", border: "border-white/10", text: "text-white/70" };
  return (
    <div className={`${tone.bg} border ${tone.border} rounded-2xl p-5 text-center`}>
      <Ic className={`w-5 h-5 ${tone.text} mx-auto mb-2`} />
      <p className="text-2xl font-bold text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{value}</p>
      <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">{label}</p>
      {sub && <p className="text-[10px] text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

function TenureRow({ icon: Ic, accent, headline, sublines, badge }) {
  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl bg-white/5 border border-white/10`}>
      <div className={`w-9 h-9 rounded-full ${accent} flex items-center justify-center shrink-0 border border-white/10`}>
        <Ic className="w-4 h-4 text-white" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-semibold text-white">{headline}</p>
          {badge && <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-medium">{badge}</span>}
        </div>
        {sublines.map((line, i) => (
          <p key={i} className="text-[11px] text-slate-400 mt-0.5">{line}</p>
        ))}
      </div>
    </div>
  );
}

export default function Hero() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [card, setCard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [copied, setCopied] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const fetchCard = useCallback(async () => {
    setSyncing(true);
    try {
      const { data } = await api.get(`/heroes/${encodeURIComponent(slug)}`);
      setCard(data);
      setNotFound(false);
    } catch (err) {
      if (err.response?.status === 404) setNotFound(true);
    } finally { setLoading(false); setSyncing(false); }
  }, [slug]);

  useEffect(() => { fetchCard(); }, [fetchCard]);

  const handleShare = async () => {
    const url = window.location.href;
    const title = card ? `${card.name} — Heroic HIFI Foundation` : "Heroic HIFI Foundation";
    if (navigator.share) {
      try { await navigator.share({ title, url }); return; } catch { /* fall through */ }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success("Recognition card link copied!");
      setTimeout(() => setCopied(false), 2500);
    } catch {
      toast.error("Could not copy. Long-press the URL to share.");
    }
  };

  if (loading) {
    return (
      <div className="bg-[#060E1A] min-h-screen flex items-center justify-center" data-testid="hero-loading">
        <div className="w-8 h-8 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
      </div>
    );
  }

  if (notFound || !card) {
    return (
      <div className="bg-[#060E1A] min-h-screen flex items-center justify-center px-6" data-testid="hero-not-found">
        <div className="text-center max-w-md">
          <Award className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-white mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Hero not found</h2>
          <p className="text-sm text-slate-400 mb-6">We couldn't find a public recognition card for that name. It may have been retired, or the link could be mistyped.</p>
          <Link to="/wall-of-fame" className="inline-flex items-center gap-2 text-sm text-amber-300 hover:text-amber-200">
            <ArrowLeft className="w-4 h-4" /> Back to Wall of Fame
          </Link>
        </div>
      </div>
    );
  }

  const totalDonated = Number(card.lifetime_total || 0);
  const feeAbsorbed = Number(card.lifetime_fee_absorbed || 0);
  const donationCount = Number(card.donation_count || 0);
  const isAdmin = !!card.is_admin;
  const hasDonated = totalDonated > 0 || donationCount > 0;
  const isMagnanimous = feeAbsorbed > 0;

  return (
    <div data-testid="hero-page" className="bg-[#060E1A] min-h-screen">
      {/* Hero header */}
      <section className="relative py-16 sm:py-24 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#1E56A0]/20 via-transparent to-transparent" />
        <div className="absolute top-20 left-10 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-48 h-48 bg-rose-500/5 rounded-full blur-3xl" />

        <div className="relative max-w-3xl mx-auto px-4 sm:px-6">
          <button onClick={() => navigate("/wall-of-fame")} className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-amber-300 mb-8" data-testid="back-to-wof">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Wall of Fame
          </button>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="text-center">
            {/* Avatar */}
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full bg-gradient-to-br from-amber-400/40 via-orange-500/40 to-rose-500/40 mx-auto flex items-center justify-center mb-5 border-4 border-amber-300/30 shadow-2xl shadow-amber-500/20">
              <span className="text-4xl sm:text-5xl font-bold text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {card.name?.charAt(0)?.toUpperCase() || "?"}
              </span>
            </div>

            {/* Role overline */}
            <span className="inline-flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/30 rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-widest text-amber-300 mb-3" data-testid="hero-role-overline">
              {isAdmin ? <Compass className="w-3 h-3" /> : <Star className="w-3 h-3" />}
              {card.role_label}
              {card.designation && <> · {card.designation}</>}
            </span>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-3" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="hero-name">
              {card.name}
            </h1>

            {/* Admins: tenure-free framing. Everyone else: subtle "Since X" */}
            {isAdmin ? (
              <p className="text-sm text-slate-400" data-testid="hero-admin-tagline">
                Serving the foundation, behind the scenes & at the front lines.
              </p>
            ) : card.joined_at ? (
              <p className="text-sm text-slate-400" data-testid="hero-since">
                Walking with us since <span className="text-slate-200">{fmtDate(card.joined_at)}</span>
              </p>
            ) : null}

            {/* Action row */}
            <div className="flex items-center justify-center gap-2 mt-7 flex-wrap">
              <button
                onClick={handleShare}
                className="inline-flex items-center gap-2 bg-amber-500/15 hover:bg-amber-500/25 border border-amber-400/40 text-amber-200 rounded-full px-5 py-2 text-sm font-medium transition-colors"
                data-testid="hero-share-btn"
              >
                {copied ? <Check className="w-4 h-4" /> : <Share2 className="w-4 h-4" />}
                {copied ? "Link Copied" : "Share"}
              </button>
              <button
                onClick={fetchCard}
                disabled={syncing}
                className="inline-flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-full px-4 py-2 text-xs disabled:opacity-50"
                title="Re-fetch the freshest data from the foundation's records"
                data-testid="hero-sync-btn"
              >
                <Sparkles className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} /> {syncing ? "Syncing…" : "Sync"}
              </button>
            </div>
            <p className="text-[10px] text-slate-500 mt-3 inline-flex items-center gap-1"><ShieldCheck className="w-3 h-3" /> Public amounts rounded to the nearest ₹100 to safeguard donor privacy.</p>
          </motion.div>
        </div>
      </section>

      {/* Magnanimity callout */}
      {isMagnanimous && (
        <section className="px-4 sm:px-6 mb-10" data-testid="magnanimity-callout">
          <div className="max-w-3xl mx-auto bg-gradient-to-br from-rose-900/40 via-pink-900/30 to-amber-900/30 border border-rose-500/30 rounded-2xl p-6 flex items-start gap-4">
            <div className="shrink-0 w-12 h-12 rounded-full bg-rose-500/20 border border-rose-400/40 flex items-center justify-center">
              <Heart className="w-5 h-5 fill-rose-300 text-rose-300" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-rose-200 font-semibold mb-1">A Special Note of Magnanimity</p>
              <p className="text-base text-white leading-relaxed" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {card.name?.split(" ")[0] || "This hero"} voluntarily absorbed <strong className="text-rose-300">₹{feeAbsorbed.toLocaleString("en-IN")}</strong> in payment-gateway fees, ensuring the foundation received <em>every rupee</em> of their contribution. A quiet, deliberate act of generosity that asks for no spotlight.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Lifetime total */}
      {hasDonated && (
        <section className="px-4 sm:px-6 mb-10" data-testid="lifetime-total-section">
          <div className="max-w-3xl mx-auto">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <StatTile icon={IndianRupee} label="Total Donated (rounded)" value={`\u20B9${totalDonated.toLocaleString("en-IN")}`} sub={donationCount > 0 ? `${donationCount} contribution${donationCount === 1 ? "" : "s"}` : ""} accent="amber" />
              {isMagnanimous && (
                <StatTile icon={Heart} label="Fees Absorbed (rounded)" value={`\u20B9${feeAbsorbed.toLocaleString("en-IN")}`} sub="So we receive every rupee" accent="rose" />
              )}
              {!isAdmin && card.volunteer_hours > 0 && (
                <StatTile icon={Clock} label="Volunteer Hours" value={card.volunteer_hours} accent="blue" />
              )}
            </div>
          </div>
        </section>
      )}

      {/* Award tenures */}
      {(card.top_donor_tenures?.length > 0 || card.most_generous_tenures?.length > 0) && (
        <section className="px-4 sm:px-6 mb-10" data-testid="award-tenures-section">
          <div className="max-w-3xl mx-auto bg-white/[0.02] border border-white/10 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-amber-300 uppercase tracking-widest mb-4 flex items-center gap-2"><Trophy className="w-3.5 h-3.5" /> Awards & Tenures</h2>
            <div className="space-y-3">
              {(card.top_donor_tenures || []).map((t) => (
                <TenureRow key={`td-${t.id}`}
                  icon={Trophy}
                  accent="bg-amber-500/30"
                  headline={`Top Donor of FY ${t.fy_label}`}
                  sublines={[
                    `Contribution (rounded): \u20B9${Number(t.peak_amount || 0).toLocaleString("en-IN")}`,
                    tenureLabel(t.awarded_at, t.ended_at),
                    t.ended_reason || null,
                  ].filter(Boolean)}
                  badge={!t.ended_at ? "Currently Holding" : null}
                />
              ))}
              {(card.most_generous_tenures || []).map((t) => (
                <TenureRow key={`mg-${t.id}`}
                  icon={Heart}
                  accent="bg-rose-500/30"
                  headline={`Most Generous Donor of FY ${t.fy_label}`}
                  sublines={[
                    `Fees absorbed (rounded): \u20B9${Number(t.peak_fee || 0).toLocaleString("en-IN")} on a pledge of \u20B9${Number(t.peak_pledge || 0).toLocaleString("en-IN")}`,
                    tenureLabel(t.awarded_at, t.ended_at),
                    t.ended_reason || null,
                  ].filter(Boolean)}
                  badge={!t.ended_at ? "Currently Holding" : null}
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Office bearer tenures (kept for everyone — even admins, since this is a formal post) */}
      {card.office_tenures?.length > 0 && (
        <section className="px-4 sm:px-6 mb-10" data-testid="office-tenures-section">
          <div className="max-w-3xl mx-auto bg-white/[0.02] border border-white/10 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-amber-300 uppercase tracking-widest mb-4 flex items-center gap-2"><Compass className="w-3.5 h-3.5" /> Office-Bearer Tenures</h2>
            <div className="space-y-3">
              {card.office_tenures.map((t) => (
                <TenureRow key={`oh-${t.id}`}
                  icon={Compass}
                  accent="bg-amber-500/25"
                  headline={t.post}
                  sublines={[
                    tenureLabel(t.start_date, t.end_date),
                    t.leadership_bio || null,
                    t.end_reason || null,
                  ].filter(Boolean)}
                  badge={!t.end_date ? "In Office" : null}
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Heroic Patron commitment (non-admins only — admins are tenure-free) */}
      {!isAdmin && card.patron_charge_count > 0 && (
        <section className="px-4 sm:px-6 mb-10" data-testid="patron-section">
          <div className="max-w-3xl mx-auto bg-gradient-to-br from-fuchsia-900/30 via-purple-900/20 to-[#0D2847] border border-fuchsia-500/30 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-fuchsia-500/25 border border-fuchsia-400/40 flex items-center justify-center shrink-0">
                <Crown className="w-5 h-5 text-fuchsia-300" />
              </div>
              <div>
                <p className="text-[10px] font-semibold text-fuchsia-300 uppercase tracking-widest mb-1">Heroic Patron</p>
                <p className="text-base text-white leading-relaxed">
                  Sustains us with <strong className="text-fuchsia-200">{card.patron_charge_count}</strong> recurring contribution{card.patron_charge_count === 1 ? "" : "s"} on the <strong className="text-fuchsia-200">{card.patron_plan}</strong> plan{card.patron_since && <>, since <strong className="text-fuchsia-200">{fmtDate(card.patron_since)}</strong></>}.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Badges */}
      {(card.badges || []).length > 0 && (
        <section className="px-4 sm:px-6 mb-10" data-testid="badges-section">
          <div className="max-w-3xl mx-auto bg-white/[0.02] border border-white/10 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-amber-300 uppercase tracking-widest mb-4 flex items-center gap-2"><Award className="w-3.5 h-3.5" /> Recognitions</h2>
            <div className="flex flex-wrap gap-2">
              {card.badges.map((b) => (
                <span key={b} className={`text-xs px-3 py-1.5 rounded-full border font-medium ${BADGE_COLORS[b] || "bg-slate-800 text-slate-300 border-slate-700"}`}>{b}</span>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Specializations (volunteers only) */}
      {!isAdmin && (card.specializations || []).length > 0 && (
        <section className="px-4 sm:px-6 mb-10" data-testid="specs-section">
          <div className="max-w-3xl mx-auto bg-white/[0.02] border border-white/10 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-amber-300 uppercase tracking-widest mb-4 flex items-center gap-2"><Sparkles className="w-3.5 h-3.5" /> Areas of Service</h2>
            <div className="flex flex-wrap gap-2">
              {card.specializations.map((s) => (
                <span key={s} className="text-xs px-3 py-1.5 rounded-full border font-medium bg-cyan-900/30 text-cyan-200 border-cyan-700/40">{s}</span>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Contribution summary */}
      {card.contribution_summary && (
        <section className="px-4 sm:px-6 mb-10" data-testid="summary-section">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-lg sm:text-xl text-slate-300/85 italic leading-relaxed" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              &ldquo;{card.contribution_summary}&rdquo;
            </p>
          </div>
        </section>
      )}

      {/* Footer sync timestamp */}
      <section className="pb-16 px-4 sm:px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-[10px] text-slate-600 inline-flex items-center gap-1.5">
            <Calendar className="w-3 h-3" /> Last synced {fmtDate(card.synced_at)} · Heroic HIFI Foundation
          </p>
        </div>
      </section>
    </div>
  );
}
