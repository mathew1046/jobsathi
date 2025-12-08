import React from 'react';
import { motion } from 'framer-motion';

const LoadingScreen = ({ message = "Loading..." }) => {
    return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white dark:bg-slate-900">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center"
            >
                <div className="relative w-24 h-24 mb-8">
                    <div className="absolute inset-0 border-4 border-gray-100 dark:border-gray-800 rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-saas-blue rounded-full border-t-transparent animate-spin"></div>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-3 h-3 bg-saas-blue rounded-full animate-pulse"></div>
                    </div>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Setting up your experience</h2>
                <p className="text-gray-500 dark:text-gray-400 animate-pulse">{message}</p>
            </motion.div>
        </div>
    );
};

export default LoadingScreen;
