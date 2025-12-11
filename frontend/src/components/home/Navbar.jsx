import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { motion } from 'framer-motion';

const Navbar = ({ darkMode, toggleDarkMode, t, onEmployerClick }) => {
    const _t = t || ((k) => k === "app_name" ? "JobSathi" : "Toggle dark mode");
    return (
        <nav className="fixed w-full z-50 top-0 start-0 border-b border-gray-200 bg-white/80 backdrop-blur-sm dark:bg-saas-dark/90 dark:border-gray-800 transition-colors duration-300">
            <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
                <div className="flex items-center">
                    <span className="text-2xl font-bold text-saas-blue dark:text-blue-400">
                        {_t("app_name")}
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={onEmployerClick}
                        className="px-4 py-2 text-sm font-medium text-white bg-saas-blue rounded-lg hover:bg-blue-700 transition-all shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-saas-blue dark:focus:ring-offset-gray-900"
                    >
                        Employer
                    </button>
                    <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={toggleDarkMode}
                        className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        aria-label={_t("toggle_dark_mode")}
                    >
                        {darkMode ? (
                            <Sun className="w-5 h-5 text-gray-400 hover:text-yellow-400 transition-colors" />
                        ) : (
                            <Moon className="w-5 h-5 text-gray-500 hover:text-saas-blue transition-colors" />
                        )}
                    </motion.button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
