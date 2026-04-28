import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { User, Award, Clock, IndianRupee, Camera, Save, Shield, Ticket, Sparkles, Lock } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";

const BADGE_COLORS = {
  "Helping Hero": "bg-green-100 text-green-800 border-green-200",
  "Century Hero": "bg-yellow-100 text-yellow-800 border-yellow-200",
  "Generous Soul": "bg-amber-100 text-amber-800 border-amber-200",
  "Community Builder": "bg-blue-100 text-blue-800 border-blue-200",
  "Star Volunteer of the Month": "bg-pink-100 text-pink-800 border-pink-200",
  "Star Volunteer of the Quarter": "bg-purple-100 text-purple-800 border-purple-200",
  "Star Volunteer of the Year": "bg-red-100 text-red-800 border-red-200",
  "Top Donor": "bg-orange-100 text-orange-800 border-orange-200",
  "Rising Star": "bg-cyan-100 text-cyan-800 border-cyan-200",
};

export default function Profile() {
  const { user, loading: authLoading } = useAuth();
  const { lang } = useLang();
  const t = translations[lang].profile;
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", address: "" });
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [picUrl, setPicUrl] = useState(null);
  const [editingSpec, setEditingSpec] = useState(false);
  const [specDraft, setSpecDraft] = useState([]);
  const [savingSpec, setSavingSpec] = useState(false);

  const SPECIALIZATIONS = [
    { key: "education", label: "Education" },
    { key: "healthcare", label: "Healthcare" },
    { key: "environment", label: "Environment" },
    { key: "food", label: "Food Distribution" },
    { key: "women", label: "Women Empowerment" },
    { key: "animal", label: "Animal Welfare" },
    { key: "clothing", label: "Clothing Drives" },
  ];

  const fetchProfile = useCallback(async () => {
    try {
      const { data } = await api.get("/profile");
      setProfile(data);
      setForm({ name: data.name || "", phone: data.phone || "", address: data.address || "" });
      if (data.profile_pic_path) {
        loadPic(data.profile_pic_path);
      }
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  }, []);

  const loadPic = async (path) => {
    try {
      const token = localStorage.getItem("hhf_token");
      const resp = await api.get(`/files/${path}`, { responseType: "blob", headers: { Authorization: `Bearer ${token}` } });
      setPicUrl(URL.createObjectURL(resp.data));
    } catch {
      setPicUrl(null);
    }
  };

  useEffect(() => { if (user) fetchProfile(); }, [user, fetchProfile]);

  if (authLoading) return null;
  if (!user) return <Navigate to="/login" replace />;

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/profile/upload-pic", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(t.pic_uploaded);
      if (data.path) loadPic(data.path);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setUploading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/profile", form);
      toast.success(t.profile_updated);
      setEditing(false);
      fetchProfile();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setSaving(false); }
  };

  const toggleDraftSpec = (key) => {
    setSpecDraft((prev) => prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]);
  };

  const handleStartSpecEdit = () => {
    setSpecDraft([...(profile.specializations || [])]);
    setEditingSpec(true);
  };

  const handleSaveSpec = async () => {
    if (specDraft.length < 3) {
      toast.error(lang === "hi" ? "कम से कम 3 क्षेत्र चुनें।" : "Pick at least 3 specializations.");
      return;
    }
    const original = new Set(profile.specializations || []);
    if (specDraft.length === original.size && specDraft.every((k) => original.has(k))) {
      toast.info(lang === "hi" ? "कोई परिवर्तन नहीं।" : "No changes to save.");
      setEditingSpec(false);
      return;
    }
    const remaining = profile.specialization_edits_remaining ?? 2;
    const msg = remaining === 1
      ? (lang === "hi" ? "यह आपका अंतिम संपादन है। पुष्टि करें?" : "This will use your LAST lifetime edit. Confirm?")
      : (lang === "hi" ? `पुष्टि करें? आपके पास ${remaining - 1} संपादन शेष होंगे।` : `Confirm? You will have ${remaining - 1} edit(s) remaining after this.`);
    if (!window.confirm(msg)) return;
    setSavingSpec(true);
    try {
      await api.put("/profile/specializations", { specializations: specDraft });
      toast.success(lang === "hi" ? "रुचि क्षेत्र अपडेट हो गए।" : "Specializations updated.");
      setEditingSpec(false);
      fetchProfile();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setSavingSpec(false); }
  };

  return (
    <div data-testid="profile-page">
      <section className="relative py-16 sm:py-20 bg-[#1E56A0]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.title}
          </h1>
        </div>
      </section>

      <section className="py-8 sm:py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          {!profile ? (
            <p className="text-center text-slate-400 py-12">{t.loading}</p>
          ) : (
            <div className="space-y-6">
              {/* Avatar + Name */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6 flex flex-col sm:flex-row items-center gap-6">
                <div className="relative group">
                  <div className="w-24 h-24 rounded-full bg-[#1E56A0]/10 flex items-center justify-center overflow-hidden border-4 border-sky-100">
                    {picUrl ? (
                      <img src={picUrl} alt="Profile" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-10 h-10 text-[#1E56A0]" />
                    )}
                  </div>
                  <label className="absolute inset-0 flex items-center justify-center bg-black/30 rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity" data-testid="upload-pic-label">
                    <Camera className="w-6 h-6 text-white" />
                    <input type="file" accept="image/*" className="hidden" onChange={handleUpload} disabled={uploading} data-testid="upload-pic-input" />
                  </label>
                </div>
                <div className="text-center sm:text-left flex-1">
                  <h2 className="text-2xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{profile.name}</h2>
                  <p className="text-sm text-slate-500">{profile.email}</p>
                  <p className="text-xs text-[#1E56A0] font-medium mt-1">{profile.role === "admin" ? t.admin : t.volunteer}</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => setEditing(!editing)} className="rounded-full gap-1" data-testid="edit-profile-btn">
                  <Save className="w-3 h-3" /> {editing ? t.cancel : t.edit}
                </Button>
              </motion.div>

              {/* Edit Form */}
              {editing && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6 space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.name}</Label>
                    <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 rounded-xl" data-testid="edit-name" />
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.phone}</Label>
                    <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="mt-1 rounded-xl" data-testid="edit-phone" />
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.address}</Label>
                    <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="mt-1 rounded-xl" data-testid="edit-address" />
                  </div>
                  <Button onClick={handleSave} disabled={saving} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full px-6" data-testid="save-profile-btn">
                    {saving ? "..." : t.save}
                  </Button>
                </motion.div>
              )}

              {/* Stats Row */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-4 text-center">
                  <Clock className="w-5 h-5 text-[#1E56A0] mx-auto mb-2" />
                  <p className="text-2xl font-bold text-[#0D2847]">{profile.volunteer_hours}</p>
                  <p className="text-xs text-slate-500">{t.hours}</p>
                </div>
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-4 text-center">
                  <IndianRupee className="w-5 h-5 text-[#FF7F00] mx-auto mb-2" />
                  <p className="text-2xl font-bold text-[#0D2847]">{(profile.total_donated || 0).toLocaleString("en-IN")}</p>
                  <p className="text-xs text-slate-500">{t.total_donated}</p>
                </div>
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-4 text-center">
                  <Award className="w-5 h-5 text-[#16A34A] mx-auto mb-2" />
                  <p className="text-2xl font-bold text-[#0D2847]">{(profile.badges || []).length}</p>
                  <p className="text-xs text-slate-500">{t.badges_count}</p>
                </div>
              </div>

              {/* Badges */}
              <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6">
                <h3 className="text-lg font-medium text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                  <Award className="w-5 h-5 text-[#FF7F00]" /> {t.badges_title}
                </h3>
                <div className="flex flex-wrap gap-2" data-testid="badges-list">
                  {(profile.badges || []).map((b) => (
                    <span key={b} className={`text-xs px-3 py-1.5 rounded-full border font-medium ${BADGE_COLORS[b] || "bg-slate-100 text-slate-700 border-slate-200"}`} data-testid={`badge-${b.replace(/\s/g, "-")}`}>
                      {b}
                    </span>
                  ))}
                  {(profile.badges || []).length === 0 && <p className="text-sm text-slate-400">{t.no_badges}</p>}
                </div>
              </div>

              {/* Specializations (volunteer only) */}
              {profile.role === "volunteer" && (
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6" data-testid="specializations-card">
                  <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
                    <div>
                      <h3 className="text-lg font-medium text-[#0D2847] flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                        <Sparkles className="w-5 h-5 text-[#FF7F00]" /> {lang === "hi" ? "मेरे रुचि क्षेत्र" : "My Specializations"}
                      </h3>
                      <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        {(profile.specialization_edits_remaining ?? 2) > 0
                          ? (lang === "hi"
                            ? `${profile.specialization_edits_remaining} आजीवन संपादन शेष`
                            : `${profile.specialization_edits_remaining} lifetime edit${profile.specialization_edits_remaining === 1 ? "" : "s"} remaining`)
                          : (lang === "hi" ? "सभी संपादन उपयोग किए जा चुके हैं" : "All lifetime edits used")}
                      </p>
                    </div>
                    {!editingSpec && (profile.specialization_edits_remaining ?? 2) > 0 && (
                      <Button variant="outline" size="sm" onClick={handleStartSpecEdit} className="rounded-full gap-1 border-sky-200" data-testid="edit-specs-btn">
                        <Save className="w-3 h-3" /> {lang === "hi" ? "संपादन" : "Edit"}
                      </Button>
                    )}
                  </div>
                  {!editingSpec ? (
                    <div className="flex flex-wrap gap-2" data-testid="specs-list">
                      {(profile.specializations || []).length === 0
                        ? <p className="text-sm text-slate-400">{lang === "hi" ? "कोई रुचि क्षेत्र नहीं चुने गए।" : "No specializations selected yet."}</p>
                        : (profile.specializations || []).map((k) => {
                          const sp = SPECIALIZATIONS.find((s) => s.key === k);
                          return (
                            <span key={k} className="text-xs px-3 py-1.5 rounded-full border font-medium bg-sky-50 text-[#1E56A0] border-sky-200" data-testid={`spec-chip-${k}`}>
                              {sp ? sp.label : k}
                            </span>
                          );
                        })}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className={`text-[11px] ${specDraft.length >= 3 ? "text-green-600" : "text-amber-600"}`} data-testid="spec-draft-count">
                        {lang === "hi" ? `${specDraft.length}/3 चयनित (न्यूनतम)` : `${specDraft.length} of 3 minimum selected`}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {SPECIALIZATIONS.map((s) => {
                          const active = specDraft.includes(s.key);
                          return (
                            <button
                              key={s.key}
                              type="button"
                              onClick={() => toggleDraftSpec(s.key)}
                              data-testid={`spec-edit-${s.key}-btn`}
                              className={`px-3 py-1.5 rounded-full text-xs font-medium border-2 transition-all ${active ? "border-[#1E56A0] bg-[#1E56A0] text-white" : "border-sky-200 text-slate-600 hover:border-sky-300"}`}
                            >
                              {s.label}
                            </button>
                          );
                        })}
                      </div>
                      <div className="flex gap-2 pt-2">
                        <Button onClick={handleSaveSpec} disabled={savingSpec || specDraft.length < 3} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full px-5 disabled:opacity-50 disabled:cursor-not-allowed" data-testid="save-specs-btn">
                          {savingSpec ? "..." : (lang === "hi" ? "सहेजें" : "Save")}
                        </Button>
                        <Button variant="outline" onClick={() => setEditingSpec(false)} className="rounded-full border-sky-200" data-testid="cancel-specs-btn">
                          {lang === "hi" ? "रद्द करें" : "Cancel"}
                        </Button>
                      </div>
                      <p className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-2">
                        ⚠️ {lang === "hi"
                          ? "ध्यान दें: आपके पास जीवन भर में केवल 2 संपादन हैं। सोच-समझकर चुनें।"
                          : "Note: You only get 2 edits in your lifetime. Choose carefully."}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Quick Links */}
              <div className="flex flex-wrap gap-3">
                <Link to="/tickets">
                  <Button variant="outline" className="rounded-full gap-2 text-sm border-sky-200" data-testid="go-to-tickets">
                    <Ticket className="w-4 h-4" /> {t.my_tickets}
                  </Button>
                </Link>
                <Link to="/community">
                  <Button variant="outline" className="rounded-full gap-2 text-sm border-sky-200" data-testid="go-to-community">
                    <Shield className="w-4 h-4" /> {t.community_link}
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
