
import React from 'react';
import { LayoutDashboard, Briefcase, Users, LogOut } from 'lucide-react';

const EmployerSidebar = ({ currentView, onViewChange, onLogout }) => {
    const navItems = [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'jobs', label: 'Jobs', icon: Briefcase },
        { id: 'applicants', label: 'Applicants', icon: Users },
    ];

    return (
        <div className="hidden md:flex flex-col w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center h-16 border-b border-gray-200 dark:border-gray-700">
                <span className="text-xl font-bold text-saas-blue">JobSathi Employer</span>
            </div>
            <div className="flex-grow flex flex-col p-4 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <button
                            key={item.id}
                            onClick={() => onViewChange(item.id)}
                            className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${currentView === item.id
                                    ? 'bg-blue-50 text-saas-blue dark:bg-blue-900/20 dark:text-blue-400'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                        >
                            <Icon className="w-5 h-5 mr-3" />
                            {item.label}
                        </button>
                    );
                })}
            </div>
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <button
                    onClick={onLogout}
                    className="flex items-center w-full px-4 py-3 text-sm font-medium text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                    <LogOut className="w-5 h-5 mr-3" />
                    Sign Out
                </button>
            </div>
        </div>
    );
};

export default EmployerSidebar;
