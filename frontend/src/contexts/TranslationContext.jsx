import React, { createContext, useState, useContext, useEffect } from 'react';

const TranslationContext = createContext();

export const useTranslation = () => useContext(TranslationContext);

export const TranslationProvider = ({ children, selectedLanguage, apiBaseUrl }) => {
  const [translations, setTranslations] = useState({});
  const [loading, setLoading] = useState(false);

  // Default English strings to be translated
  // Ideally, these should be gathered from the app, but for now we list common ones
  const defaultStrings = {
    "welcome_title": "Find Your Next Job with Your Voice",
    "welcome_subtitle": "No resume needed. Just speak.",
    "start_button": "Start Now",
    "recording_start": "Tap to Speak",
    "recording_stop": "Stop Recording",
    "processing": "Processing...",
    "next_question": "Next Question",
    "skip_question": "Skip",
    "submit": "Submit",
    "resume_ready": "Your Resume is Ready!",
    "download_resume": "Download Resume",
    "search_jobs": "Search Jobs",
    // Add more keys as needed
  };

  useEffect(() => {
    const fetchTranslations = async () => {
      if (selectedLanguage === 'en') {
        setTranslations(defaultStrings);
        return;
      }

      setLoading(true);
      try {
        const response = await fetch(`${apiBaseUrl}/ui-translations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            language: selectedLanguage,
            elements: defaultStrings
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setTranslations(data.translations);
        } else {
          console.error("Failed to fetch translations");
          setTranslations(defaultStrings); // Fallback
        }
      } catch (error) {
        console.error("Translation error:", error);
        setTranslations(defaultStrings); // Fallback
      } finally {
        setLoading(false);
      }
    };

    fetchTranslations();
  }, [selectedLanguage, apiBaseUrl]);

  const t = (key) => {
    return translations[key] || defaultStrings[key] || key;
  };

  return (
    <TranslationContext.Provider value={{ t, loading }}>
      {children}
    </TranslationContext.Provider>
  );
};
