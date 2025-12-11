
import React, { useEffect, useState } from 'react';
import { mockEmployerApi } from '../../services/mockEmployerApi';
import { UserCheck, Clock, CheckCircle, Briefcase } from 'lucide-react';

const EmployerApplicants = () => {
    const [applicants, setApplicants] = useState([]);
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [assignModal, setAssignModal] = useState({ show: false, applicantId: null });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        const [appsData, jobsData] = await Promise.all([
            mockEmployerApi.getApplicants(),
            mockEmployerApi.getJobs()
        ]);
        setApplicants(appsData);
        setJobs(jobsData);
        setLoading(false);
    };

    const handleAssign = async (jobId) => {
        await mockEmployerApi.assignApplicant(assignModal.applicantId, jobId);
        setAssignModal({ show: false, applicantId: null });
        loadData();
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Applicant Management</h1>

            <div className="grid gap-4">
                {applicants.map((app) => (
                    <div key={app.id} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-start space-x-4">
                            <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-full">
                                <UserCheck className="w-6 h-6 text-saas-blue" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{app.name}</h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">{app.experience} Experience • {app.phone}</p>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {app.skills.map(skill => (
                                        <span key={skill} className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-md">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center space-x-4">
                            <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center ${app.status === 'Hired'
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                                }`}>
                                {app.status === 'Hired' ? <CheckCircle className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                                {app.status}
                            </div>

                            {app.status !== 'Hired' && (
                                <button
                                    onClick={() => setAssignModal({ show: true, applicantId: app.id })}
                                    className="px-4 py-2 bg-saas-blue text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    Assign Job
                                </button>
                            )}

                            {app.status === 'Hired' && (
                                <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                                    <Briefcase className="w-4 h-4 mr-1" />
                                    Job #{app.assignedJob}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Assignment Modal */}
            {assignModal.show && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-sm w-full p-6">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Assign Candidate</h2>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                            {jobs.filter(j => j.status === 'Active').map(job => (
                                <button
                                    key={job.id}
                                    onClick={() => handleAssign(job.id)}
                                    className="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-600 transition-colors"
                                >
                                    <div className="font-medium text-gray-900 dark:text-white">{job.title}</div>
                                    <div className="text-xs text-gray-500">{job.location}</div>
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={() => setAssignModal({ show: false, applicantId: null })}
                            className="mt-4 w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmployerApplicants;
