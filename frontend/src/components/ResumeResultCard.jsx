import React from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Search, ExternalLink, Briefcase } from 'lucide-react';

const ResumeResultCard = ({
    profile,
    isBuilding,
    statusMessage,
    onRestart,
    onSearchJobs,
    isSearchingJobs,
    jobs,
    showJobs,
    t
}) => {
    const _t = t || ((k) => k);

    // Loading State
    if (isBuilding) {
        return (
            <div className="flex justify-center w-full px-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-10 text-center border border-gray-200 dark:border-gray-700"
                >
                    <div className="relative w-16 h-16 mx-auto mb-4">
                        <div className="absolute inset-0 border-4 border-gray-200 dark:border-gray-700 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{_t("creating_resume")}</h3>
                    <p className="text-gray-500 dark:text-gray-400">{statusMessage || _t("processing_details")}</p>
                </motion.div>
            </div>
        );
    }

    // No profile state
    if (!profile) {
        return (
            <div className="flex justify-center w-full px-4">
                <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-10 text-center border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-500 dark:text-gray-400">No profile data available</p>
                    <button
                        onClick={onRestart}
                        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                        Start Over
                    </button>
                </div>
            </div>
        );
    }

    // Helper to render any value nicely
    const renderValue = (value) => {
        if (value === null || value === undefined) return <span className="text-gray-400 italic">Not provided</span>;
        if (Array.isArray(value)) {
            if (value.length === 0) return <span className="text-gray-400 italic">None</span>;
            return (
                <ul className="list-disc list-inside space-y-1">
                    {value.map((item, idx) => (
                        <li key={idx} className="text-gray-700 dark:text-gray-300">
                            {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                        </li>
                    ))}
                </ul>
            );
        }
        if (typeof value === 'object') {
            return <pre className="text-sm bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-x-auto">{JSON.stringify(value, null, 2)}</pre>;
        }
        return <span className="text-gray-800 dark:text-gray-200">{String(value)}</span>;
    };

    // Job card component
    const JobCard = ({ job }) => (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start gap-3 mb-3">
                <div className="flex-1">
                    <h4 className="font-bold text-gray-900 dark:text-white text-lg">{job.title}</h4>
                    <p className="text-blue-600 dark:text-blue-400 font-medium">{job.company}</p>
                </div>
                {job.location && (
                    <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded-full whitespace-nowrap">
                        {job.location}
                    </span>
                )}
            </div>
            
            {job.description && (
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-3">{job.description}</p>
            )}
            
            <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                    {job.salary && job.salary !== "Not specified" && (
                        <span className="font-medium text-green-600 dark:text-green-400">💰 {job.salary}</span>
                    )}
                    {job.source && <span>via {job.source}</span>}
                </div>
                {job.url && (
                    <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium"
                    >
                        Apply <ExternalLink className="w-3 h-3" />
                    </a>
                )}
            </div>
        </div>
    );

    // Fields to display from profile
    const profileFields = [
        { key: 'name', label: 'Name' },
        { key: 'role', label: 'Desired Role' },
        { key: 'email', label: 'Email' },
        { key: 'phone', label: 'Phone' },
        { key: 'location', label: 'Location' },
        { key: 'work_authorization', label: 'Work Authorization' },
        { key: 'summary', label: 'Summary' },
        { key: 'skills', label: 'Skills' },
        { key: 'machines_operated', label: 'Machines/Vehicles' },
        { key: 'certifications', label: 'Certifications' },
        { key: 'shift_availability', label: 'Shift Availability' },
        { key: 'start_date', label: 'Available From' },
        { key: 'transportation', label: 'Transportation' },
        { key: 'physical_capabilities', label: 'Physical Capabilities' },
        { key: 'experience_years', label: 'Years of Experience' },
        { key: 'experience_details', label: 'Work Experience' },
        { key: 'languages', label: 'Languages' },
        { key: 'work_type_preference', label: 'Work Type' },
        { key: 'referrals', label: 'References' },
        { key: 'education', label: 'Education' },
    ];

    return (
        <div className="w-full max-w-4xl mx-auto px-4 pb-16">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-t-2xl p-6 text-white"
            >
                <h2 className="text-2xl font-bold mb-1">✅ Profile Created Successfully!</h2>
                <p className="text-blue-100">Your information has been extracted. Review below and search for jobs.</p>
            </motion.div>

            {/* Profile Data Card */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 border-t-0 rounded-b-2xl shadow-lg"
            >
                {/* Profile Fields */}
                <div className="p-6 space-y-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-3">
                        📋 Your Profile Data
                    </h3>
                    
                    <div className="grid gap-4">
                        {profileFields.map(({ key, label }) => {
                            const value = profile[key];
                            // Skip if null/undefined/empty array
                            if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) {
                                return null;
                            }
                            return (
                                <div key={key} className="border-b border-gray-100 dark:border-gray-700 pb-3 last:border-0">
                                    <div className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-1 uppercase tracking-wide">
                                        {label}
                                    </div>
                                    <div className="text-gray-800 dark:text-gray-200">
                                        {renderValue(value)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Raw JSON Toggle */}
                    <details className="mt-6 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <summary className="cursor-pointer p-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
                            🔍 View Raw JSON Data
                        </summary>
                        <pre className="p-4 text-xs overflow-x-auto text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-b-lg">
                            {JSON.stringify(profile, null, 2)}
                        </pre>
                    </details>
                </div>

                {/* Actions */}
                <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-3">
                    <button
                        onClick={onSearchJobs}
                        disabled={isSearchingJobs}
                        className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold px-5 py-3 rounded-xl transition-colors"
                    >
                        {isSearchingJobs ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                Finding Jobs...
                            </>
                        ) : (
                            <>
                                <Search className="w-4 h-4" />
                                Search Jobs
                            </>
                        )}
                    </button>
                    
                    <button
                        onClick={onRestart}
                        className="flex items-center gap-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-medium px-5 py-3 rounded-xl transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Start Over
                    </button>
                </div>
            </motion.div>

            {/* Jobs Section */}
            {showJobs && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="mt-8"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <Briefcase className="w-6 h-6 text-green-600" />
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                            Job Matches ({jobs?.length || 0})
                        </h3>
                    </div>

                    {jobs && jobs.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {jobs.map((job, idx) => (
                                <JobCard key={idx} job={job} />
                            ))}
                        </div>
                    ) : (
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center">
                            <p className="text-yellow-700 dark:text-yellow-300">
                                No jobs found matching your profile. Try updating your skills or location.
                            </p>
                        </div>
                    )}
                </motion.div>
            )}
        </div>
    );
};

export default ResumeResultCard;
