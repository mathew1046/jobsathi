
// Mock data and service for Employer Dashboard

// Mock Jobs
let jobs = [
    {
        id: 1,
        title: "Forklift Operator",
        location: "Guwahati, Assam",
        type: "Full-time",
        salary: "₹15,000 - ₹20,000",
        status: "Active",
        posted: "2023-10-15",
        applicants: 12,
        description: "Experienced forklift operator needed for warehouse operations so."
    },
    {
        id: 2,
        title: "Construction Helper",
        location: "Dispur, Assam",
        type: "Contract",
        salary: "₹500/day",
        status: "Active",
        posted: "2023-10-18",
        applicants: 8,
        description: "General helper for construction site."
    },
    {
        id: 3,
        title: "Security Guard",
        location: "Sareygag, Assam",
        type: "Full-time",
        salary: "₹12,000/month",
        status: "Closed",
        posted: "2023-09-01",
        applicants: 25,
        description: "Night shift security guard."
    }
];

// Mock Applicants
let applicants = [
    {
        id: 101,
        name: "Ramesh Kumar",
        skills: ["Heavy Lifting", "Construction"],
        experience: "3 years",
        status: "New",
        appliedTo: 2,
        phone: "+91 9876543210"
    },
    {
        id: 102,
        name: "Sunita Devi",
        skills: ["Cleaning", "Organizing"],
        experience: "5 years",
        status: "Interviewed",
        appliedTo: 3,
        phone: "+91 9876543211"
    },
    {
        id: 103,
        name: "Rahul Singh",
        skills: ["Forklift", "Driving"],
        experience: "2 years",
        status: "New",
        appliedTo: 1,
        phone: "+91 9876543212"
    }
];

export const mockEmployerApi = {
    login: async (email, password) => {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                if (email === 'employer@jobsathi.com' && password === 'admin') {
                    resolve({ name: 'TechBuild Construction', email });
                } else {
                    reject(new Error('Invalid credentials'));
                }
            }, 800);
        });
    },

    getStats: async () => {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    totalJobs: jobs.length,
                    activeJobs: jobs.filter(j => j.status === 'Active').length,
                    totalApplicants: applicants.length,
                    interviewsScheduled: 5
                });
            }, 500);
        });
    },

    getJobs: async () => {
        return new Promise((resolve) => setTimeout(() => resolve([...jobs]), 500));
    },

    createJob: async (jobData) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const newJob = {
                    ...jobData,
                    id: Date.now(),
                    applicants: 0,
                    posted: new Date().toISOString().split('T')[0],
                    status: 'Active'
                };
                jobs = [newJob, ...jobs];
                resolve(newJob);
            }, 500);
        });
    },

    deleteJob: async (id) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                jobs = jobs.filter(j => j.id !== id);
                resolve(true);
            }, 500);
        });
    },

    getApplicants: async () => {
        return new Promise((resolve) => setTimeout(() => resolve([...applicants]), 500));
    },

    assignApplicant: async (applicantId, jobId) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                applicants = applicants.map(app =>
                    app.id === applicantId ? { ...app, status: 'Hired', assignedJob: jobId } : app
                );
                resolve(true);
            }, 500);
        });
    }
};
