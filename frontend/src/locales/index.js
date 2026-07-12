import en from "./en.json";
import hi from "./hi.json";
import hinglish from "./hinglish.json";

const dictionaries = { en, hi, hinglish };

const formatters = {
  en: {
    showingCharts: (visible, total) => `Showing ${visible} of ${total} visualizations`,
    forecastGenerated: (count) => `Forecast engine generated ${count} prediction signals. Review the charts page for demand and trend projections.`,
    cleanedDatasetApplied: (filename) => `Cleaned dataset applied: ${filename}`,
    basicChatUsage: (used, limit) => `Basic chatbot usage: ${used}/${limit} questions`,
    trialEndsIn: (days) => `Trial ends in ${days} day${days === 1 ? "" : "s"}`,
    premiumRenewsIn: (days) => `Premium renews in ${days} day${days === 1 ? "" : "s"}`,
  },
  hi: {
    showingCharts: (visible, total) => `${total} में से ${visible} विजुअलाइजेशन दिख रहे हैं`,
    forecastGenerated: (count) => `फोरकास्ट इंजन ने ${count} प्रेडिक्शन संकेत बनाए हैं. डिमांड और ट्रेंड प्रोजेक्शन के लिए चार्ट पेज देखें.`,
    cleanedDatasetApplied: (filename) => `क्लीन डेटासेट लागू हुआ: ${filename}`,
    basicChatUsage: (used, limit) => `Basic चैटबॉट उपयोग: ${used}/${limit} सवाल`,
    trialEndsIn: (days) => `ट्रायल ${days} दिन में समाप्त होगा`,
    premiumRenewsIn: (days) => `Premium ${days} दिन में रिन्यू होगा`,
  },
  hinglish: {
    showingCharts: (visible, total) => `${visible} of ${total} visualizations dikhaye jaan rahe hain`,
    forecastGenerated: (count) => `Forecast engine ne ${count} prediction signals banaye hain. Charts page dekho.`,
    cleanedDatasetApplied: (filename) => `Clean dataset apply ho gaya: ${filename}`,
    basicChatUsage: (used, limit) => `Basic chatbot usage: ${used}/${limit} questions`,
    trialEndsIn: (days) => `Trial ${days} din mein expire hoga`,
    premiumRenewsIn: (days) => `Premium ${days} din mein renew hoga`,
  },
};

export function getTranslations(language) {
  const normalized = Object.prototype.hasOwnProperty.call(dictionaries, language) ? language : "en";
  return {
    ...dictionaries.en,
    ...dictionaries[normalized],
    ...formatters.en,
    ...formatters[normalized],
  };
}
