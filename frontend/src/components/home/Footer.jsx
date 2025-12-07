import React from 'react';
import { Heart } from 'lucide-react';

const Footer = () => {
    return (
        <footer className="py-6 relative z-10 border-t border-slate-200 dark:border-white/10 bg-white/80 dark:bg-slate-900/50 backdrop-blur-sm transition-colors duration-300">
            <div className="max-w-screen-xl mx-auto px-4 text-center">
                <p className="flex items-center justify-center text-sm font-medium text-slate-600 dark:text-slate-400">
                    Made with <Heart className="w-4 h-4 mx-1 text-blue-600 dark:text-blue-500 fill-current animate-pulse" /> by Team Arrakis
                </p>
            </div>
        </footer>
    );
};

export default Footer;
