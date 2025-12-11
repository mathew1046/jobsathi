
import React, { useState } from 'react';
import EmployerLogin from './EmployerLogin';
import EmployerSidebar from './EmployerSidebar';
import EmployerOverview from './EmployerOverview';
import EmployerJobs from './EmployerJobs';
import EmployerApplicants from './EmployerApplicants';
import { Menu } from 'lucide-react';

const EmployerDashboard = ({ onBackToHome }) => {
    const [user, setUser] = useState(null);
    const [currentView, setCurrentView] = useState('overview');
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    if (!user) {
        return (
            <div className="relative">
                <button
                    onClick={onBackToHome}
                    className="absolute top-4 left-4 text-gray-600 dark:text-gray-400 hover:text-saas-blue"
                >
                    &larr; Back to Home
                </button>
                <EmployerLogin onLogin={setUser} />
            </div>
        );
    }

    const renderView = () => {
        switch (currentView) {
            case 'overview': return <EmployerOverview />;
            case 'jobs': return <EmployerJobs />;
            case 'applicants': return <EmployerApplicants />;
            default: return <EmployerOverview />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
            {/* Sidebar for Desktop */}
            <EmployerSidebar
                currentView={currentView}
                onViewChange={setCurrentView}
                onLogout={() => setUser(null)}
            />

            {/* Mobile Header */}
            <div className="md:hidden fixed top-0 w-full bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 z-50 px-4 py-3 flex justify-between items-center">
                <span className="font-bold text-saas-blue">JobSathi Employer</span>
                <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                    <Menu className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                </button>
            </div>

            {/* Mobile Menu Overlay */}
            {isMobileMenuOpen && (
                <div className="md:hidden fixed inset-0 z-40 bg-black/50" onClick={() => setIsMobileMenuOpen(false)}>
                    <div className="w-64 h-full bg-white dark:bg-gray-800 pt-16" onClick={e => e.stopPropagation()}>
                        <EmployerSidebar
                            currentView={currentView}
                            onViewChange={(view) => {
                                setCurrentView(view);
                                setIsMobileMenuOpen(false);
                            }}
                            onLogout={() => setUser(null)}
                        />
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto h-screen pt-16 md:pt-0">
                <div className="p-6 max-w-7xl mx-auto">
                    {renderView()}
                </div>
            </main>
        </div>
    );
};

export default EmployerDashboard;
