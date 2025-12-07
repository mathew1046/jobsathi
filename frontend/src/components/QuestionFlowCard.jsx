import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AudioRecorder from './AudioRecorder';
import { Mic, MessageSquare, SkipForward, AlertCircle } from 'lucide-react';

const QuestionFlowCard = ({
    currentQuestion,
    currentIndex,
    totalQuestions,
    audioControl, // { isPlaying, onPlayPlay, onReplay, audioAvailable, error, questionAudio }
    recordingControl, // { isProcessing, statusMessage, onRecordingComplete, onRecordStart }
    textControl, // { textAnswer, setTextAnswer, onSubmit }
    onSkip,
    onRestart,
    error
}) => {
    const progress = ((currentIndex + 1) / totalQuestions) * 100;

    return (
        <div className="flex justify-center w-full px-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="w-full max-w-2xl bg-white dark:bg-saas-dark-card rounded-3xl shadow-2xl overflow-hidden border border-gray-100 dark:border-gray-700"
            >
                {/* Header / Progress */}
                <div className="bg-gray-50 dark:bg-slate-800/50 px-8 py-6 border-b border-gray-100 dark:border-gray-700">
                    <div className="flex justify-between items-center mb-4">
                        <span className="text-sm font-semibold tracking-wider text-gray-500 dark:text-gray-400 uppercase">
                            Building Your Resume
                        </span>
                        <span className="text-sm font-bold text-saas-blue dark:text-blue-400">
                            Q{currentIndex + 1} <span className="text-gray-400 font-normal">/ {totalQuestions}</span>
                        </span>
                    </div>
                    <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.5 }}
                            className="h-full bg-saas-blue rounded-full"
                        />
                    </div>
                </div>

                {/* Content */}
                <div className="p-8 md:p-10">
                    {/* Question Text */}
                    <div className="mb-8">
                        <motion.h2
                            key={currentQuestion.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-3"
                        >
                            {currentQuestion.question}
                        </motion.h2>
                        <p className="text-gray-500 dark:text-gray-400 text-lg">
                            {currentQuestion.prompt}
                        </p>
                    </div>

                    {/* Audio Playback Controls (TTS) */}
                    {audioControl.audioAvailable && audioControl.questionAudio && (
                        <div className="flex items-center gap-3 mb-8 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-xl w-fit">
                            <button
                                onClick={audioControl.onPlayPause}
                                className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-blue-800 rounded-lg text-sm font-semibold text-saas-blue dark:text-blue-200 shadow-sm hover:shadow transition-shadow"
                            >
                                {audioControl.isPlaying ? (
                                    <>
                                        <span className="animate-pulse">🔊</span> Playing
                                    </>
                                ) : (
                                    <>▶️ Listen</>
                                )}
                            </button>
                            <button
                                onClick={audioControl.onReplay}
                                className="p-1.5 text-gray-500 hover:text-saas-blue transition-colors"
                                title="Replay"
                            >
                                Start Over ↺
                            </button>
                        </div>
                    )}

                    <div className="space-y-8">
                        {/* Divider OR */}
                        <div className="relative flex items-center py-2">
                            <div className="flex-grow border-t border-gray-200 dark:border-gray-700"></div>
                            <span className="flex-shrink-0 mx-4 text-gray-400 text-sm font-medium uppercase tracking-widest">
                                Answer With Voice
                            </span>
                            <div className="flex-grow border-t border-gray-200 dark:border-gray-700"></div>
                        </div>

                        {/* Recorder Component */}
                        <div className="flex justify-center">
                            <AudioRecorder
                                onRecordingComplete={recordingControl.onRecordingComplete}
                                onRecordStart={recordingControl.onRecordStart}
                                disabled={recordingControl.isProcessing}
                            />
                        </div>

                        {/* Divider OR */}
                        <div className="relative flex items-center py-2">
                            <div className="flex-grow border-t border-gray-200 dark:border-gray-700"></div>
                            <span className="flex-shrink-0 mx-4 text-gray-400 text-sm font-medium uppercase tracking-widest">
                                Or Type Answer
                            </span>
                            <div className="flex-grow border-t border-gray-200 dark:border-gray-700"></div>
                        </div>

                        {/* Text Input */}
                        <div className="relative">
                            <textarea
                                value={textControl.textAnswer}
                                onChange={(e) => textControl.setTextAnswer(e.target.value)}
                                disabled={recordingControl.isProcessing}
                                placeholder="Type your answer here..."
                                rows={4}
                                className="w-full p-4 pl-12 rounded-xl bg-gray-50 dark:bg-slate-900 border-2 border-transparent focus:border-saas-blue focus:bg-white dark:focus:bg-slate-800 transition-all outline-none resize-none text-gray-900 dark:text-white placeholder-gray-400"
                            />
                            <MessageSquare className="absolute top-4 left-4 w-5 h-5 text-gray-400" />
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col sm:flex-row gap-4 pt-2">
                            <button
                                onClick={textControl.onSubmit}
                                disabled={recordingControl.isProcessing || !textControl.textAnswer.trim()}
                                className="flex-1 bg-saas-blue text-white font-bold py-3.5 px-6 rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                            >
                                Submit Written Answer
                            </button>
                            <button
                                onClick={onSkip}
                                disabled={recordingControl.isProcessing}
                                className="px-6 py-3.5 rounded-xl font-semibold text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
                            >
                                Skip <SkipForward className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Status Messages */}
                    <AnimatePresence>
                        {(recordingControl.isProcessing || recordingControl.statusMessage) && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mt-6 flex flex-col items-center justify-center text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl"
                            >
                                {recordingControl.isProcessing && (
                                    <div className="flex space-x-1 mb-2">
                                        <div className="w-2 h-2 bg-saas-blue rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                                        <div className="w-2 h-2 bg-saas-blue rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-2 h-2 bg-saas-blue rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    </div>
                                )}
                                <p className="text-saas-blue font-medium">{recordingControl.statusMessage}</p>
                            </motion.div>
                        )}

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0 }}
                                className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex items-center gap-3"
                            >
                                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                <p>{error}</p>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <div className="mt-8 text-center">
                        <button
                            onClick={onRestart}
                            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                            disabled={recordingControl.isProcessing}
                        >
                            Start Over
                        </button>
                    </div>

                </div>
            </motion.div>
        </div>
    );
};

export default QuestionFlowCard;
