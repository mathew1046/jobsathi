import React from 'react';
import { motion } from 'framer-motion';
import { Download, RefreshCw, MapPin, Mail, Phone, Briefcase, GraduationCap, Award, User } from 'lucide-react';

const ResumeResultCard = ({
    profile,
    isBuilding,
    statusMessage,
    onRestart,
    apiBaseUrl,
    t
}) => {
    const _t = t || ((k) => k);

    // Loading State
    if (isBuilding || !profile) {
        return (
            <div className="flex justify-center w-full px-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="w-full max-w-2xl bg-white dark:bg-saas-dark-card rounded-3xl shadow-xl p-12 text-center border border-gray-100 dark:border-gray-700"
                >
                    <div className="relative w-20 h-20 mx-auto mb-6">
                        <div className="absolute inset-0 border-4 border-gray-100 dark:border-gray-700 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-saas-blue rounded-full border-t-transparent animate-spin"></div>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{_t("creating_resume")}</h3>
                    <p className="text-gray-500 dark:text-gray-400 animate-pulse">{statusMessage || _t("processing_details")}</p>
                </motion.div>
            </div>
        );
    }

    // Helper for Safely rendering lists/strings
    const renderList = (data) => {
        if (!data) return null;
        if (Array.isArray(data)) return data;
        if (typeof data === 'string') return data.split(',').map(i => i.trim());
        return [JSON.stringify(data)];
    };

    const containerVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.6, ease: "easeOut", staggerChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <div className="flex justify-center w-full px-4 pb-20">
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="w-full max-w-4xl bg-white dark:bg-saas-dark-card rounded-3xl shadow-2xl border border-gray-100 dark:border-gray-700 overflow-hidden"
            >
                {/* Header Section */}
                <div className="bg-gray-50 dark:bg-slate-800/80 px-8 py-8 md:px-12 border-b border-gray-200 dark:border-gray-700 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                            {_t("resume_title")}
                        </h2>
                        <p className="text-gray-500 dark:text-gray-400">
                            {_t("resume_subtitle")}
                        </p>
                    </div>

                    {profile.pdf_filename && (
                        <motion.a
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            href={`${apiBaseUrl}/download_resume/${profile.pdf_filename}`}
                            download
                            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg shadow-green-600/20 transition-all"
                        >
                            <Download className="w-5 h-5" /> {_t("download_pdf")}
                        </motion.a>
                    )}
                </div>

                {/* Content Body */}
                <div className="p-8 md:p-12 space-y-10">

                    {/* Personal Info Grid */}
                    <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-gray-700">
                            <div className="flex items-center gap-2 mb-1 text-saas-blue dark:text-blue-400">
                                <User className="w-4 h-4" /> <span className="text-xs font-bold uppercase tracking-wider">{_t("label_name")}</span>
                            </div>
                            <div className="font-semibold text-gray-900 dark:text-white">{profile.name || "N/A"}</div>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-gray-700">
                            <div className="flex items-center gap-2 mb-1 text-saas-blue dark:text-blue-400">
                                <Briefcase className="w-4 h-4" /> <span className="text-xs font-bold uppercase tracking-wider">{_t("label_role")}</span>
                            </div>
                            <div className="font-semibold text-gray-900 dark:text-white">{profile.role || "N/A"}</div>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-gray-700">
                            <div className="flex items-center gap-2 mb-1 text-saas-blue dark:text-blue-400">
                                <Mail className="w-4 h-4" /> <span className="text-xs font-bold uppercase tracking-wider">{_t("label_email")}</span>
                            </div>
                            <div className="font-semibold text-gray-900 dark:text-white truncate" title={profile.email}>{profile.email || "N/A"}</div>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-gray-700">
                            <div className="flex items-center gap-2 mb-1 text-saas-blue dark:text-blue-400">
                                <Phone className="w-4 h-4" /> <span className="text-xs font-bold uppercase tracking-wider">{_t("label_phone")}</span>
                            </div>
                            <div className="font-semibold text-gray-900 dark:text-white">{profile.phone || "N/A"}</div>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-gray-700 md:col-span-2 lg:col-span-1">
                            <div className="flex items-center gap-2 mb-1 text-saas-blue dark:text-blue-400">
                                <MapPin className="w-4 h-4" /> <span className="text-xs font-bold uppercase tracking-wider">{_t("label_location")}</span>
                            </div>
                            <div className="font-semibold text-gray-900 dark:text-white">{profile.location || "N/A"}</div>
                        </div>
                    </motion.div>

                    {/* Summary */}
                    {profile.summary && (
                        <motion.div variants={itemVariants}>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-saas-blue rounded-full"></span>
                                {_t("section_summary")}
                            </h3>
                            <div className="bg-gray-50 dark:bg-slate-800/50 p-6 rounded-2xl text-gray-700 dark:text-gray-300 leading-relaxed">
                                {profile.summary}
                            </div>
                        </motion.div>
                    )}

                    {/* Skills Pills */}
                    {profile.skills && (
                        <motion.div variants={itemVariants}>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-saas-blue rounded-full"></span>
                                {_t("section_skills")}
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {renderList(profile.skills).map((skill, idx) => (
                                    <motion.span
                                        key={idx}
                                        whileHover={{ scale: 1.05 }}
                                        className="px-4 py-2 bg-blue-50 dark:bg-blue-900/30 text-saas-blue dark:text-blue-300 rounded-full text-sm font-semibold border border-blue-100 dark:border-blue-800 cursor-default"
                                    >
                                        {typeof skill === 'object' ? JSON.stringify(skill) : String(skill)}
                                    </motion.span>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Experience Timeline */}
                    {profile.experience_details && (
                        <motion.div variants={itemVariants}>
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                    <span className="w-1 h-6 bg-saas-blue rounded-full"></span>
                                    {_t("section_experience")}
                                </h3>
                                {profile.experience_years && (
                                    <span className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1 rounded-full text-sm font-medium">
                                        {profile.experience_years} {_t("years_total")}
                                    </span>
                                )}
                            </div>

                            <div className="space-y-4">
                                {renderList(profile.experience_details).map((exp, idx) => (
                                    <div key={idx} className="group relative pl-8 border-l-2 border-gray-200 dark:border-gray-700 hover:border-saas-blue transition-colors">
                                        <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white dark:bg-slate-900 border-2 border-gray-300 dark:border-gray-600 group-hover:border-saas-blue transition-colors"></div>
                                        <div className="mb-1">
                                            <h4 className="text-lg font-bold text-gray-900 dark:text-white">
                                                {typeof exp === 'object' ? (exp.role || 'Role') : String(exp)}
                                            </h4>
                                            {typeof exp === 'object' && (
                                                <div className="text-sm font-medium text-saas-blue dark:text-blue-400 mb-2">
                                                    {exp.company} {exp.duration ? `• ${exp.duration}` : ''}
                                                </div>
                                            )}
                                        </div>
                                        {typeof exp === 'object' && exp.description && (
                                            <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                                                {exp.description}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Education */}
                    {profile.education && (
                        <motion.div variants={itemVariants}>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                                <span className="w-1 h-6 bg-saas-blue rounded-full"></span>
                                {_t("section_education")}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {renderList(profile.education).map((edu, idx) => (
                                    <div key={idx} className="bg-gray-50 dark:bg-slate-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 flex items-start gap-4">
                                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-saas-blue dark:text-blue-400">
                                            <GraduationCap className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-gray-900 dark:text-white">
                                                {typeof edu === 'object' ? (edu.degree || 'Degree') : String(edu)}
                                            </h4>
                                            {typeof edu === 'object' && (
                                                <>
                                                    <p className="text-sm text-gray-600 dark:text-gray-400">{edu.institution}</p>
                                                    {edu.year && <span className="text-xs font-semibold text-gray-400 mt-1 block">{edu.year}</span>}
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Certifications (if any) */}
                    {profile.certifications && (
                        <motion.div variants={itemVariants}>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-saas-blue rounded-full"></span>
                                {_t("section_certifications")}
                            </h3>
                            <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-6">
                                <ul className="space-y-3">
                                    {renderList(profile.certifications).map((cert, idx) => (
                                        <li key={idx} className="flex items-start gap-3 text-gray-700 dark:text-gray-300">
                                            <Award className="w-5 h-5 text-saas-blue dark:text-blue-400 flex-shrink-0 mt-0.5" />
                                            <span>{typeof cert === 'object' ? JSON.stringify(cert) : String(cert)}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </motion.div>
                    )}

                    {/* Footer Actions */}
                    <motion.div variants={itemVariants} className="pt-8 border-t border-gray-100 dark:border-gray-800 flex justify-center">
                        <button
                            onClick={onRestart}
                            className="flex items-center gap-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors font-medium px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800"
                        >
                            <RefreshCw className="w-4 h-4" /> {_t("start_new_resume")}
                        </button>
                    </motion.div>

                </div>
            </motion.div>
        </div>
    );
};

export default ResumeResultCard;
