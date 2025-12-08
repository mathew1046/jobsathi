import React from 'react';
import { motion } from 'framer-motion';
import { Rocket, BrainCircuit, CheckCircle, Download } from 'lucide-react';

const HeroSection = ({ onStart, t }) => {
    const _t = t || ((k) => k); // Fallback
    return (
        <div className="flex flex-col justify-center text-left py-12 lg:py-0">
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <h1 className="max-w-3xl mb-6 text-5xl font-extrabold tracking-tight leading-tight text-gray-900 dark:text-white md:text-6xl">
                    <span className="text-saas-blue dark:text-blue-400">{_t("hero_title_1")}</span><br />
                    {_t("hero_title_2")}<br />
                    {_t("hero_title_3")}<br />
                    {_t("hero_title_4")}
                </h1>

                <p className="max-w-2xl mb-8 text-lg font-normal text-gray-600 dark:text-gray-300 leading-relaxed">
                    {_t("hero_subtitle")}
                </p>

                {/* CTA Button */}
                <div className="mb-16">
                    <motion.button
                        whileHover={{ y: -2 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={onStart}
                        className="inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-white transition-all duration-200 bg-saas-blue rounded-full shadow-lg hover:bg-saas-blue-dark hover:shadow-xl dark:bg-blue-600 dark:hover:bg-blue-700"
                    >
                        <span className="mr-2">{_t("start_building")}</span>
                        <Rocket className="w-5 h-5" />
                    </motion.button>
                </div>

                {/* Feature Icons */}
                <div className="flex flex-wrap gap-12 md:gap-16 pt-8 border-t border-gray-100 dark:border-gray-800">
                    <FeatureItem icon={BrainCircuit} label={_t("feature_ai")} subLabel={_t("feature_precision")} />
                    <FeatureItem icon={CheckCircle} label={_t("feature_ats")} subLabel="" />
                    <FeatureItem icon={Download} label={_t("feature_instant")} subLabel={_t("feature_download")} />
                </div>
            </motion.div>
        </div>
    );
};

const FeatureItem = ({ icon: Icon, label, subLabel }) => (
    <div className="flex flex-col items-center group cursor-default">
        <div className="mb-4 p-3 rounded-2xl bg-white shadow-card group-hover:shadow-card-hover transition-shadow dark:bg-saas-dark-card dark:shadow-none">
            <Icon className="w-8 h-8 text-saas-blue dark:text-blue-400" />
        </div>
        <div className="text-center">
            <div className="font-bold text-gray-900 dark:text-white text-sm md:text-base">{label}</div>
            {subLabel && <div className="font-bold text-gray-900 dark:text-white text-sm md:text-base">{subLabel}</div>}
        </div>
    </div>
);

export default HeroSection;
