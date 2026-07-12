import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import axios from "axios";
import Plot from "react-plotly.js";
import "./Dashboard.css";
import Auth from "./Auth";
import Profile from "./Profile";
import VoiceAssistantButton from "./components/VoiceAssistantButton";
import ModalPortal from "./components/ModalPortal";
import { useLanguage } from "./language/LanguageContext";
import {
  LANGUAGE_BUTTON_LABELS,
  LANGUAGE_SEQUENCE,
  getLanguageHeaders,
} from "./language/languageSystem";

import { API_BASE } from "./config/api";
import { getTranslations } from "./locales";

const CHART_TYPES = ["all", "histogram", "bar", "line", "box", "scatter", "pie", "heatmap", "forecast"];
const APP_NAME = "Data Mantri";


const COLUMN_TERMS = {
  hi: {
    product: "प्रोडक्ट",
    products: "प्रोडक्ट",
    category: "कैटेगरी",
    categories: "कैटेगरी",
    city: "शहर",
    customer: "ग्राहक",
    customers: "ग्राहक",
    order: "ऑर्डर",
    date: "तारीख",
    name: "नाम",
    price: "कीमत",
    amount: "राशि",
    revenue: "रेवेन्यू",
    sales: "बिक्री",
    sale: "बिक्री",
    profit: "लाभ",
    quantity: "मात्रा",
    count: "गिनती",
    percent: "प्रतिशत",
    percentage: "प्रतिशत",
    total: "कुल",
    average: "औसत",
    avg: "औसत",
    discount: "डिस्काउंट",
    region: "क्षेत्र",
    state: "राज्य",
    segment: "सेगमेंट",
    row: "पंक्ति",
    rows: "पंक्तियाँ",
    column: "कॉलम",
    columns: "कॉलम",
    correlation: "सह-संबंध",
    distribution: "वितरण",
  },
  hinglish: {
    product: "product",
    products: "products",
    category: "category",
    categories: "categories",
    city: "city",
    customer: "customer",
    customers: "customers",
    order: "order",
    date: "date",
    name: "name",
    price: "price",
    amount: "amount",
    revenue: "revenue",
    sales: "sales",
    sale: "sales",
    profit: "profit",
    quantity: "quantity",
    count: "count",
    percent: "percent",
    percentage: "percentage",
    total: "total",
    average: "average",
    avg: "average",
    discount: "discount",
    region: "region",
    state: "state",
    segment: "segment",
    row: "row",
    rows: "rows",
    column: "column",
    columns: "columns",
    correlation: "correlation",
    distribution: "distribution",
  },
};

const PHRASE_TRANSLATIONS = {
  hi: [
    ["Dataset size overview", "डेटासेट आकार सारांश"],
    ["Duplicate data detected", "डुप्लिकेट डेटा मिला"],
    ["Missing values are present", "मिसिंग वैल्यू मौजूद हैं"],
    ["Data is ready for analysis", "डेटा विश्लेषण के लिए तैयार है"],
    ["Fill missing values", "मिसिंग वैल्यू भरें"],
    ["Remove duplicate rows", "डुप्लिकेट पंक्तियाँ हटाएँ"],
    ["Check dates and trends", "तारीख और ट्रेंड जाँचें"],
    ["Use more data if possible", "संभव हो तो ज्यादा डेटा इस्तेमाल करें"],
    ["Keep the dataset clean and monitor it", "डेटासेट को साफ रखें और मॉनिटर करें"],
    ["Check numbers for", "इन नंबरों को जाँचें:"],
    ["Check", "जाँचें"],
    ["balance", "का संतुलन"],
    ["High concentration in", "उच्च एकाग्रता:"],
    ["Most common", "सबसे आम"],
    ["is right-skewed", "में बड़े वैल्यू का असर ज्यादा है"],
    ["is left-skewed", "में छोटे वैल्यू का असर दिख रहा है"],
    ["dominates", "में सबसे ज्यादा है"],
    ["Business Advisor report", "बिजनेस एडवाइजर रिपोर्ट"],
    ["Top Actions", "शीर्ष कार्य"],
    ["Recommendations", "सुझाव"],
    ["Recommendation details", "सिफारिश विवरण"],
    ["View Details", "विवरण देखें"],
    ["Implementation status", "कार्यान्वयन स्थिति"],
    ["Owner", "जिम्मेदार व्यक्ति"],
    ["Business lead", "व्यावसायिक प्रमुख"],
    ["Business Lead", "व्यावसायिक प्रमुख"],
    ["Owner alignment", "जिम्मेदार व्यक्ति की सहमति"],
    ["KPI baseline", "KPI आधार रेखा"],
    ["Execution capacity", "कार्यान्वयन क्षमता"],
    ["Mark Complete", "पूर्ण चिह्नित करें"],
    ["Export PDF", "PDF निर्यात करें"],
    ["Create Task", "कार्य बनाएँ"],
    ["Implement", "लागू करें"],
    ["Dependencies", "निर्भरताएँ"],
    ["Notes", "नोट्स"],
    ["Expected ROI", "उम्मीदित ROI"],
    ["Timeline", "समयरेखा"],
    ["Difficulty", "कठिनाई"],
    ["Business problem", "व्यावसायिक समस्या"],
    ["AI reasoning", "एआई का तर्क"],
    ["Expected revenue", "अनुमानित राजस्व"],
    ["Expected cost", "अनुमानित लागत"],
    ["Evidence", "सबूत"],
    ["Implementation checklist", "कार्यान्वयन जाँच सूची"],
    ["Potential risks", "संभावित जोखिम"],
    ["Success metrics", "सफलता मापदंड"],
    ["Recommended action", "सिफ़ारिशित कार्रवाई"],
    ["Related KPIs", "संबंधित KPI"],
    ["Current Value", "वर्तमान मूल्य"],
    ["Trend", "ट्रेंड"],
    ["Forecast", "पूर्वानुमान"],
    ["Confidence", "कॉन्फिडेंस"],
    ["Confidence explanation", "कॉन्फिडेंस स्पष्टीकरण"],
    ["No recommendations available yet.", "अभी कोई सुझाव उपलब्ध नहीं है."],
    ["No prioritized actions available yet.", "अभी कोई प्राथमिकता वाला कार्य उपलब्ध नहीं है."],
    ["Your free advisor has reviewed your data and created clear recommendations below.", "आपके मुफ्त एडवाइजर ने डेटा देखकर साफ सुझाव तैयार किए हैं."],
    ["Restoring your latest dashboard", "आपका पिछला डैशबोर्ड वापस लोड हो रहा है"],
    ["Loading saved dataset, KPIs, charts, and insights.", "सेव डेटासेट, KPIs, चार्ट और इनसाइट्स लोड हो रहे हैं."],
    ["Business Advisor report is ready. Scroll down to view it.", "बिजनेस एडवाइजर रिपोर्ट तैयार है. देखने के लिए नीचे स्क्रॉल करें."],
    ["Failed to generate Business Advisor report", "बिजनेस एडवाइजर रिपोर्ट नहीं बन सकी"],
    ["report", "रिपोर्ट"],
    ["Hide report", "रिपोर्ट छुपाएँ"],
    ["Close", "बंद करें"],
    ["Usage", "उपयोग"],
    ["Premium workspace: unlimited usage", "Premium वर्कस्पेस: अनलिमिटेड उपयोग"],
    ["Free plan usage limits", "Free प्लान उपयोग सीमा"],
    ["Unlimited", "अनलिमिटेड"],
    ["left", "बाकी"],
    ["used", "इस्तेमाल"],
    ["Unlock unlimited", "अनलिमिटेड अनलॉक करें"],
    ["Monthly", "मासिक"],
    ["Yearly", "वार्षिक"],
    ["Unlimited uploads", "अनलिमिटेड अपलोड"],
    ["Unlimited chatbot", "अनलिमिटेड चैटबॉट"],
    ["Unlimited Mitra voice", "अनलिमिटेड Mitra voice"],
    ["Unlimited reports", "अनलिमिटेड रिपोर्ट"],
    ["Prioritized action", "प्राथमिकता वाला कार्य"],
    ["Premium recommendations preview the next best action for this dataset.", "Premium सुझाव इस डेटासेट के अगले अच्छे कदम दिखाते हैं."],
    ["Revenue momentum", "रेवेन्यू मोमेंटम"],
    ["Advanced spike and drop detection appears here for Premium workspaces.", "Premium वर्कस्पेस के लिए एडवांस्ड स्पाइक और ड्रॉप डिटेक्शन यहाँ दिखेगा."],
    ["Business Advisor summary is ready", "बिजनेस एडवाइजर सारांश तैयार है"],
    ["Review the top actions and recommendations below.", "नीचे शीर्ष कार्य और सुझाव देखें."],
    ["BUSINESS ADVISOR SUMMARY", "बिजनेस एडवाइजर सारांश"],
    ["DATASET OVERVIEW", "डेटासेट ओवरव्यू"],
    ["KEY PERFORMANCE INDICATORS", "मुख्य KPI"],
    ["TOP INSIGHTS", "मुख्य इनसाइट्स"],
    ["RECOMMENDED ACTIONS", "सुझाए गए कार्य"],
    ["Next Step", "अगला कदम"],
    ["Total Records", "कुल रिकॉर्ड"],
    ["Total Columns", "कुल कॉलम"],
    ["Duplicate Rows", "डुप्लिकेट पंक्तियाँ"],
    ["Missing Values", "मिसिंग वैल्यू"],
    ["confidence", "कॉन्फिडेंस"],
    ["Impact", "इम्पैक्ट"],
    ["High", "हाई"],
    ["Medium", "मीडियम"],
    ["Low", "लो"],
    ["Confirm the affected segment and baseline KPI.", "प्रभावित सेगमेंट और बेसलाइन KPI की पुष्टि करें."],
    ["Define the first business intervention and expected outcome.", "पहला व्यावसायिक हस्तक्षेप और अपेक्षित परिणाम तय करें."],
    ["Assign an owner and weekly decision cadence.", "जिम्मेदार व्यक्ति और साप्ताहिक निर्णय प्रक्रिया तय करें."],
    ["Assign an owner, define the affected segment, launch the first intervention, and measure lift within", "जिम्मेदार व्यक्ति तय करें, प्रभावित सेगमेंट पहचानें, पहला हस्तक्षेप शुरू करें और इस अवधि में सुधार मापें:"],
    ["confidence is based on the dataset signal strength, input quality, and operational relevance.", "विश्वास स्तर डेटासेट संकेत, इनपुट गुणवत्ता और संचालनिक प्रासंगिकता पर आधारित है."],
    ["This score represents how confident the AI is in the generated insight based on the available data.", "यह स्कोर दिखाता है कि उपलब्ध डेटा के आधार पर AI इस इनसाइट को लेकर कितना आश्वस्त है."],
  ],
  hinglish: [
    ["Dataset size overview", "Dataset size summary"],
    ["Duplicate data detected", "Duplicate data mila"],
    ["Missing values are present", "Missing values present hain"],
    ["Data is ready for analysis", "Data analysis ke liye ready hai"],
    ["Fill missing values", "Missing values fill karo"],
    ["Remove duplicate rows", "Duplicate rows remove karo"],
    ["Check dates and trends", "Dates aur trends check karo"],
    ["Use more data if possible", "Possible ho to aur data use karo"],
    ["Keep the dataset clean and monitor it", "Dataset clean rakho aur monitor karo"],
    ["Check numbers for", "Numbers check karo:"],
    ["Business Advisor report", "Business Advisor report"],
    ["Top Actions", "Top actions"],
    ["Recommendations", "Recommendations"],
    ["Recommendation details", "Recommendation details"],
    ["View Details", "View Details"],
    ["Implementation status", "Implementation status"],
    ["Owner alignment", "Owner alignment"],
    ["KPI baseline", "KPI baseline"],
    ["Execution capacity", "Execution capacity"],
    ["Mark Complete", "Complete mark karo"],
    ["Export PDF", "PDF export karo"],
    ["Create Task", "Task create karo"],
    ["Implement", "Implement karo"],
    ["Dependencies", "Dependencies"],
    ["Notes", "Notes"],
    ["Expected ROI", "Expected ROI"],
    ["Timeline", "Timeline"],
    ["Difficulty", "Difficulty"],
    ["Business problem", "Business problem"],
    ["AI reasoning", "AI reasoning"],
    ["Expected revenue", "Expected revenue"],
    ["Expected cost", "Expected cost"],
    ["Evidence", "Evidence"],
    ["Implementation checklist", "Implementation checklist"],
    ["Potential risks", "Potential risks"],
    ["Success metrics", "Success metrics"],
    ["Recommended action", "Recommended action"],
    ["Related KPIs", "Related KPIs"],
    ["Current Value", "Current Value"],
    ["Trend", "Trend"],
    ["Forecast", "Forecast"],
    ["Confidence", "Confidence"],
    ["Confidence explanation", "Confidence explanation"],
    ["No recommendations available yet.", "Abhi recommendations available nahi hain."],
    ["No prioritized actions available yet.", "Abhi prioritized actions available nahi hain."],
    ["Your free advisor has reviewed your data and created clear recommendations below.", "Aapke free advisor ne data review karke clear recommendations banayi hain."],
    ["Restoring your latest dashboard", "Aapka latest dashboard restore ho raha hai"],
    ["Loading saved dataset, KPIs, charts, and insights.", "Saved dataset, KPIs, charts aur insights load ho rahe hain."],
    ["Business Advisor report is ready. Scroll down to view it.", "Business Advisor report ready hai. Dekhne ke liye neeche scroll karo."],
    ["Failed to generate Business Advisor report", "Business Advisor report generate nahi ho saki"],
    ["report", "report"],
    ["Hide report", "Report hide karo"],
    ["Close", "Close karo"],
    ["Usage", "Usage"],
    ["Premium workspace: unlimited usage", "Premium workspace: unlimited usage"],
    ["Free plan usage limits", "Free plan usage limits"],
    ["Unlimited", "Unlimited"],
    ["left", "left"],
    ["used", "used"],
    ["Unlock unlimited", "Unlimited unlock karo"],
    ["Monthly", "Monthly"],
    ["Yearly", "Yearly"],
    ["Unlimited uploads", "Unlimited uploads"],
    ["Unlimited chatbot", "Unlimited chatbot"],
    ["Unlimited Mitra voice", "Unlimited Mitra voice"],
    ["Unlimited reports", "Unlimited reports"],
    ["Prioritized action", "Prioritized action"],
    ["Confirm the affected segment and baseline KPI.", "Affected segment aur baseline KPI confirm karo."],
    ["Define the first business intervention and expected outcome.", "First business intervention aur expected outcome define karo."],
    ["Assign an owner and weekly decision cadence.", "Owner assign karo aur weekly decision cadence set karo."],
    ["Assign an owner, define the affected segment, launch the first intervention, and measure lift within", "Owner assign karo, affected segment define karo, first intervention launch karo, aur lift measure karo within"],
    ["confidence is based on the dataset signal strength, input quality, and operational relevance.", "confidence dataset signal strength, input quality aur operational relevance par based hai."],
    ["This score represents how confident the AI is in the generated insight based on the available data.", "Ye score batata hai ki available data ke basis par AI is insight par kitna confident hai."],
    ["Premium recommendations preview the next best action for this dataset.", "Premium recommendations is dataset ke next best actions dikhate hain."],
    ["Revenue momentum", "Revenue momentum"],
    ["Advanced spike and drop detection appears here for Premium workspaces.", "Premium workspace ke liye advanced spike aur drop detection yahan dikhega."],
    ["Business Advisor summary is ready", "Business Advisor summary ready hai"],
    ["Review the top actions and recommendations below.", "Neeche top actions aur recommendations dekho."],
    ["BUSINESS ADVISOR SUMMARY", "Business Advisor Summary"],
    ["DATASET OVERVIEW", "Dataset Overview"],
    ["KEY PERFORMANCE INDICATORS", "Key KPIs"],
    ["TOP INSIGHTS", "Top Insights"],
    ["RECOMMENDED ACTIONS", "Recommended Actions"],
    ["Next Step", "Next step"],
    ["Total Records", "Total records"],
    ["Total Columns", "Total columns"],
    ["Duplicate Rows", "Duplicate rows"],
    ["Missing Values", "Missing values"],
    ["confidence", "confidence"],
    ["Impact", "impact"],
  ],
};

const REGEX_TRANSLATIONS = {
  hi: [
    [/There is no such information available in the dataset\.?/gi, "इस डेटासेट में ऐसी जानकारी उपलब्ध नहीं है।"],
    [/Your dataset contains ([\d,]+) records across ([\d,]+) columns\./gi, "आपके डेटासेट में $1 रिकॉर्ड और $2 कॉलम हैं।"],
    [/Your dataset has ([\d,]+) rows across ([\d,]+) columns\./gi, "आपके डेटासेट में $1 पंक्तियाँ और $2 कॉलम हैं।"],
    [/Your dataset has ([\d,]+) rows and ([\d,]+) columns\./gi, "आपके डेटासेट में $1 पंक्तियाँ और $2 कॉलम हैं।"],
    [/Data health is ([\d.]+)\/100, with ([\d.]+)% duplicates and ([\d.]+)% missing values\./gi, "डेटा हेल्थ $1/100 है, जिसमें $2% डुप्लिकेट और $3% मिसिंग वैल्यू हैं।"],
    [/([^.!?\n]+?) leads the dataset with ([\d.]+)% share\./g, "$1 डेटासेट में $2% हिस्सेदारी के साथ सबसे आगे है।"],
    [/Forecast engine generated (\d+) prediction signals\. Review the charts page for demand and trend projections\./gi, "फोरकास्ट इंजन ने $1 भविष्यवाणी संकेत बनाए हैं। डिमांड और ट्रेंड प्रोजेक्शन के लिए चार्ट पेज देखें।"],
    [/There are ([\d,]+) duplicate rows \(([\d.]+)%\)\./gi, "$1 डुप्लिकेट पंक्तियाँ ($2%) मिलीं।"],
    [/Your dataset has ([\d,]+) missing values\./gi, "आपके डेटासेट में $1 मिसिंग वैल्यू हैं।"],
    [/([^.!?\n]+?) appears most often in ([^,\n.]+), showing up in ([\d,]+) rows \(([\d.]+)% of the dataset\)\./g, "$1, $2 में सबसे ज्यादा आता है और $3 पंक्तियों ($4%) में दिखता है।"],
    [/This means ([^.\n]+?) is concentrated around this value, so it is a sensible place to start your drill-down\./gi, (_, col) => `इसका मतलब ${localizeColumnLabel(col, "hi")} इसी वैल्यू के आसपास केंद्रित है, इसलिए गहराई से जाँच शुरू करने के लिए यह अच्छा बिंदु है।`],
    [/Use revenue, quantity, profit, or another business metric before treating it as the best-performing segment\./gi, "इसे सबसे अच्छा प्रदर्शन करने वाला सेगमेंट मानने से पहले रेवेन्यू, मात्रा, लाभ या किसी अन्य बिजनेस मेट्रिक से तुलना करें।"],
    [/The top category in ([^.\n]+) accounts for ([\d.]+)% of values\./gi, "$1 में शीर्ष कैटेगरी $2% वैल्यू बनाती है।"],
    [/The leading ([^.\n]+?) by total ([^.\n]+?) is '([^']+)'\. It contributes ([\d,.]+), representing ([\d.]+)% of the measured total\./gi, (_, segment, metric, value, amount, share) => `कुल ${localizeColumnLabel(metric, "hi")} के आधार पर सबसे आगे ${localizeColumnLabel(segment, "hi")} '${value}' है। इसका योगदान ${amount} है, जो कुल का ${share}% है।`],
    [/This is your strongest segment and a good candidate for deeper retention, inventory, or campaign analysis\./gi, "यह आपका मजबूत सेगमेंट है, इसलिए ग्राहक बनाए रखने, स्टॉक और अभियान विश्लेषण के लिए इसे पहले देखें।"],
    [/The top ([^.\n]+?) is '([^']+)' with ([\d,]+) rows \(([\d.]+)% of the dataset\)\./gi, "शीर्ष $1 '$2' है, जो $3 पंक्तियों ($4%) में आता है।"],
    [/The highest value is ([\d,.]+) in ([^.\n]+)\./gi, "$2 में सबसे ऊँची वैल्यू $1 है।"],
    [/The average value for ([^.\n]+?) is ([\d,.]+), while the median is ([\d,.]+)\./gi, (_, col, avg, median) => `${localizeColumnLabel(col, "hi")} का औसत ${avg} है और मीडियन ${median} है।`],
    [/Found ([\d,]+) outliers in ([^()]+) \(([\d.]+)% of rows\)\./gi, "$2 में $1 आउटलायर मिले, जो पंक्तियों का $3% है।"],
    [/No significant outliers detected in ([^.\n]+)\./gi, "$1 में कोई बड़ा आउटलायर नहीं मिला।"],
    [/Data quality looks ([^:]+): ([\d.]+)% of cells are missing and there are ([\d,]+) duplicate rows/gi, "डेटा क्वालिटी $1 दिख रही है: $2% सेल मिसिंग हैं और $3 डुप्लिकेट पंक्तियाँ हैं"],
    [/My suggestion: focus first on '([^']+)' in ([^.\n]+?) because it contributes ([\d,.]+), about ([\d.]+)% of the measured ([^.\n]+)\./gi, (_, value, segment, amount, share, metric) => `मेरा सुझाव: पहले ${localizeColumnLabel(segment, "hi")} में '${value}' पर ध्यान दें, क्योंकि इसका योगदान ${amount} है, जो मापे गए ${localizeColumnLabel(metric, "hi")} का लगभग ${share}% है।`],
    [/This is enough to summarize structure, profile quality, and identify the highest-signal segments before deeper modeling\./gi, "यह डेटा की संरचना, गुणवत्ता और सबसे महत्वपूर्ण सेगमेंट समझने के लिए पर्याप्त है।"],
    [/The mean of ([^.\n]+?) is noticeably higher than the median\. A small number of large values are pulling the average upward, so median, percentile, and outlier views will be more trustworthy than average alone\./gi, (_, col) => `${localizeColumnLabel(col, "hi")} का औसत मीडियन से काफी ज्यादा है। कुछ बहुत बड़े वैल्यू औसत को ऊपर खींच रहे हैं, इसलिए केवल औसत के बजाय मीडियन, पर्सेंटाइल और आउटलायर व्यू ज्यादा भरोसेमंद होंगे।`],
    [/The median of ([^.\n]+?) is higher than the mean, which suggests values are clustered toward the higher end with lower values dragging the average down\. Investigate the bottom segment before interpreting performance\./gi, (_, col) => `${localizeColumnLabel(col, "hi")} का मीडियन औसत से ज्यादा है। इसका मतलब है कि ज्यादातर वैल्यू ऊपर की तरफ हैं और कुछ कम वैल्यू औसत को नीचे ला रही हैं। प्रदर्शन समझने से पहले नीचे वाले सेगमेंट की जाँच करें।`],
    [/([^\n.]+?) makes up ([\d.]+)% of ([^\n.]+)\. Make sure this big group is not hiding smaller, important groups\./gi, (_, value, share, col) => `${value}, ${localizeColumnLabel(col, "hi")} का ${share}% हिस्सा बनाता है। ध्यान रखें कि यह बड़ा समूह छोटे लेकिन महत्वपूर्ण समूहों को छुपा न दे।`],
    [/([^\n.]+?) makes up ([\d.]+)% of ([^\n.]+)\. That means the data is very one-sided\. Double-check smaller groups before making a decision\./gi, (_, value, share, col) => `${value}, ${localizeColumnLabel(col, "hi")} का ${share}% हिस्सा बनाता है। डेटा काफी एक तरफ झुका हुआ है, इसलिए निर्णय लेने से पहले छोटे समूहों को भी जाँचें।`],
    [/([^\n.]+?) makes up ([\d.]+)% of ([^\n.]+)\. This strong share may hide a second important group, so look at the smaller parts too\./gi, (_, value, share, col) => `${value}, ${localizeColumnLabel(col, "hi")} का ${share}% हिस्सा बनाता है। यह बड़ा हिस्सा किसी दूसरे महत्वपूर्ण समूह को छुपा सकता है, इसलिए छोटे हिस्सों को भी देखें।`],
    [/Look at ([^\n.]+?) closely\. If a few values are much bigger or much smaller than the rest, your averages may not tell the full story\./gi, (_, col) => `${localizeColumnLabel(col, "hi")} को ध्यान से देखें। अगर कुछ वैल्यू बाकी से बहुत ज्यादा या कम हैं, तो औसत पूरी तस्वीर नहीं बताएगा।`],
    [/([^\n.]+?) has many small values and a few very large ones\. The average is pulled up by large numbers, so use median or smaller groups for better business decisions\./gi, (_, col) => `${localizeColumnLabel(col, "hi")} में कई छोटी वैल्यू और कुछ बहुत बड़ी वैल्यू हैं। बड़े नंबर औसत को ऊपर खींचते हैं, इसलिए बेहतर निर्णय के लिए मीडियन या छोटे समूह देखें।`],
    [/([^\n.]+?) changes a lot from row to row\. This means it is not stable, so check for unusual values before making forecasts\./gi, (_, col) => `${localizeColumnLabel(col, "hi")} पंक्ति दर पंक्ति काफी बदलता है। इसका मतलब यह स्थिर नहीं है, इसलिए पूर्वानुमान से पहले असामान्य वैल्यू जाँचें।`],
    [/Some values are empty\. Fill or replace them so your report numbers and decisions are based on real data\./gi, "कुछ वैल्यू खाली हैं। उन्हें भरें या बदलें ताकि रिपोर्ट और निर्णय भरोसेमंद डेटा पर आधारित हों।"],
    [/Some rows repeat the same information\. Remove duplicates to keep your totals and percentages accurate\./gi, "कुछ पंक्तियाँ वही जानकारी दोहरा रही हैं। कुल और प्रतिशत सही रखने के लिए डुप्लिकेट हटाएँ।"],
    [/These rows can inflate counts, distort category rankings, and make KPIs look stronger than they really are\. Remove or reconcile them before making decisions\./gi, "ये पंक्तियाँ गिनती बढ़ा सकती हैं, श्रेणी रैंकिंग बिगाड़ सकती हैं और KPIs को असल से ज्यादा मजबूत दिखा सकती हैं। निर्णय से पहले इन्हें हटाएँ या मिलाएँ।"],
    [/Columns with missing data should be reviewed by business meaning: numeric gaps can use median\/mean imputation, while category gaps usually need an 'Unknown' bucket or source-system correction\./gi, "जिन कॉलम में डेटा मिसिंग है उन्हें बिजनेस मतलब के आधार पर देखें: न्यूमेरिक gap में मीडियन/औसत भर सकते हैं, और श्रेणी gap में आम तौर पर 'Unknown' bucket या source-system सुधार चाहिए।"],
    [/This concentration means overall performance may be heavily shaped by one segment, so decisions should separate this leader from the long tail before acting\./gi, "इस एकाग्रता का मतलब है कि कुल प्रदर्शन एक ही सेगमेंट से ज्यादा प्रभावित हो सकता है, इसलिए निर्णय से पहले इस प्रमुख समूह और बाकी छोटे समूहों को अलग-अलग देखें।"],
    [/This is meaningful concentration: compare its quality, revenue, or frequency against smaller segments to avoid one-size-fits-all planning\./gi, "यह महत्वपूर्ण एकाग्रता है: एक ही योजना लागू करने से बचने के लिए इसकी गुणवत्ता, रेवेन्यू या आवृत्ति को छोटे सेगमेंट से तुलना करें।"],
    [/A small number of large values are pulling the average upward, so median, percentile, and outlier views will be more trustworthy than average alone\./gi, "कुछ बड़े वैल्यू औसत को ऊपर खींच रहे हैं, इसलिए सिर्फ औसत की जगह मीडियन, पर्सेंटाइल और आउटलायर व्यू ज्यादा भरोसेमंद होंगे।"],
    [/Investigate the bottom segment before interpreting performance\./gi, "प्रदर्शन समझने से पहले नीचे वाले सेगमेंट की जाँच करें।"],
    [/Your data has dates\. Make sure the pattern over time is real and not just one one-day jump\./gi, "आपके डेटा में तारीखें हैं। समय के साथ दिख रहा पैटर्न वास्तविक है या सिर्फ एक दिन की उछाल, यह जाँचें।"],
    [/If your file is small, the results can change a lot when you add more rows\. More data gives more reliable answers\./gi, "अगर फाइल छोटी है, तो अधिक पंक्तियाँ जोड़ने पर परिणाम काफी बदल सकते हैं। ज्यादा डेटा अधिक भरोसेमंद जवाब देता है।"],
    [/Your dataset is healthy\. Continue monitoring quality and add more data over time to improve business confidence\./gi, "आपका डेटासेट स्वस्थ है। गुणवत्ता मॉनिटर करते रहें और समय के साथ ज्यादा डेटा जोड़ें ताकि बिजनेस भरोसा बढ़े।"],
    [/(\d+) insights,\s*(\d+) recommendations/gi, "$1 इनसाइट्स, $2 सुझाव"],
    [/Cleaned data: removed (\d+) duplicates, filled (\d+) missing values/gi, "क्लीन डेटा: $1 डुप्लिकेट हटे, $2 मिसिंग वैल्यू भरी गईं"],
  ],
  hinglish: [
    [/There is no such information available in the dataset\.?/gi, "Is dataset me aisi information available nahi hai."],
    [/Your dataset contains ([\d,]+) records across ([\d,]+) columns\./gi, "Aapke dataset mein $1 records aur $2 columns hain."],
    [/Your dataset has ([\d,]+) rows across ([\d,]+) columns\./gi, "Aapke dataset mein $1 rows aur $2 columns hain."],
    [/Your dataset has ([\d,]+) rows and ([\d,]+) columns\./gi, "Aapke dataset mein $1 rows aur $2 columns hain."],
    [/Data health is ([\d.]+)\/100, with ([\d.]+)% duplicates and ([\d.]+)% missing values\./gi, "Data health $1/100 hai, jisme $2% duplicates aur $3% missing values hain."],
    [/([^.!?\n]+?) leads the dataset with ([\d.]+)% share\./g, "$1 dataset mein $2% share ke saath lead kar raha hai."],
    [/Forecast engine generated (\d+) prediction signals\. Review the charts page for demand and trend projections\./gi, "Forecast engine ne $1 prediction signals banaye hain. Demand aur trend projections ke liye charts page dekho."],
    [/There are ([\d,]+) duplicate rows \(([\d.]+)%\)\./gi, "$1 duplicate rows ($2%) mile hain."],
    [/Your dataset has ([\d,]+) missing values\./gi, "Aapke dataset mein $1 missing values hain."],
    [/([^.!?\n]+?) appears most often in ([^,\n.]+), showing up in ([\d,]+) rows \(([\d.]+)% of the dataset\)\./g, "$1, $2 mein sabse zyada aata hai aur $3 rows ($4%) mein dikhta hai."],
    [/The top category in ([^.\n]+) accounts for ([\d.]+)% of values\./gi, "$1 mein top category $2% values banati hai."],
    [/The leading ([^.\n]+?) by total ([^.\n]+?) is '([^']+)'\. It contributes ([\d,.]+), representing ([\d.]+)% of the measured total\./gi, "Total $2 ke hisaab se leading $1 '$3' hai. Iska contribution $4 hai, yani total ka $5%."],
    [/The top ([^.\n]+?) is '([^']+)' with ([\d,]+) rows \(([\d.]+)% of the dataset\)\./gi, "Top $1 '$2' hai, jo $3 rows ($4%) mein aata hai."],
    [/The highest value is ([\d,.]+) in ([^.\n]+)\./gi, "$2 mein highest value $1 hai."],
    [/The average value for ([^.\n]+?) is ([\d,.]+), while the median is ([\d,.]+)\./gi, "$1 ka average $2 hai aur median $3 hai."],
    [/Found ([\d,]+) outliers in ([^()]+) \(([\d.]+)% of rows\)\./gi, "$2 mein $1 outliers mile, jo rows ka $3% hai."],
    [/No significant outliers detected in ([^.\n]+)\./gi, "$1 mein koi major outlier nahi mila."],
    [/Data quality looks ([^:]+): ([\d.]+)% of cells are missing and there are ([\d,]+) duplicate rows/gi, "Data quality $1 lag rahi hai: $2% cells missing hain aur $3 duplicate rows hain"],
    [/My suggestion: focus first on '([^']+)' in ([^.\n]+?) because it contributes ([\d,.]+), about ([\d.]+)% of the measured ([^.\n]+)\./gi, "Mera suggestion: pehle $2 mein '$1' par focus karo, kyunki iska contribution $3 hai, measured $5 ka lagbhag $4%."],
    [/(\d+) insights,\s*(\d+) recommendations/gi, "$1 insights, $2 recommendations"],
    [/Cleaned data: removed (\d+) duplicates, filled (\d+) missing values/gi, "Clean data: $1 duplicates remove hue, $2 missing values fill hui"],
  ],
};

function humanizeDatasetLabel(value) {
  return String(value ?? "")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b(id|kpi|csv|ai|pdf)\b/gi, (match) => match.toUpperCase())
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function localizeColumnLabel(value, language) {
  const label = humanizeDatasetLabel(value);
  if (language === "en") return label;
  const terms = COLUMN_TERMS[language] || {};
  return label
    .split(" ")
    .map((word) => {
      const lower = word.toLowerCase();
      return terms[lower] || word;
    })
    .join(" ");
}

function localizeBusinessTerms(text, language) {
  if (!text || language === "en") return text;
  const directTerms = language === "hi"
    ? [
        ["Total Amount", "कुल राशि"],
        ["Order Date", "ऑर्डर तारीख"],
        ["Customer ID", "ग्राहक ID"],
        ["Product Name", "उत्पाद नाम"],
        ["Product", "उत्पाद"],
        ["Category", "श्रेणी"],
        ["City", "शहर"],
        ["Date", "तारीख"],
        ["Amount", "राशि"],
        ["Price", "कीमत"],
        ["Revenue", "रेवेन्यू"],
        ["Sales", "बिक्री"],
        ["sales", "बिक्री"],
        ["Profit", "लाभ"],
        ["profit", "लाभ"],
        ["Quantity", "मात्रा"],
        ["quantity", "मात्रा"],
        ["Count", "गिनती"],
        ["Average", "औसत"],
        ["average", "औसत"],
        ["Median", "मीडियन"],
        ["median", "मीडियन"],
        ["Forecast", "पूर्वानुमान"],
        ["forecast", "पूर्वानुमान"],
        ["Performance", "प्रदर्शन"],
        ["performance", "प्रदर्शन"],
        ["business metric", "बिजनेस मेट्रिक"],
        ["best-performing segment", "सबसे अच्छा प्रदर्शन करने वाला सेगमेंट"],
        ["drill-down", "गहराई से जाँच"],
        ["percentile", "पर्सेंटाइल"],
        ["outlier", "आउटलायर"],
        ["views", "व्यू"],
        ["Dataset", "डेटासेट"],
        ["dataset", "डेटासेट"],
        ["columns", "कॉलम"],
        ["records", "रिकॉर्ड"],
        ["rows", "पंक्तियाँ"],
        ["missing values", "मिसिंग वैल्यू"],
        ["duplicate rows", "डुप्लिकेट पंक्तियाँ"],
      ]
    : [
        ["Total Amount", "total amount"],
        ["Order Date", "order date"],
      ];

  return directTerms.reduce((current, [source, target]) => {
    const escaped = source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return current.replace(new RegExp(`\\b${escaped}\\b`, "gi"), target);
  }, text);
}

function applyLiteralReplacements(text, language) {
  return (PHRASE_TRANSLATIONS[language] || []).reduce(
    (current, [source, target]) => current.split(source).join(target),
    text
  );
}

function localizeGeneratedText(value, language) {
  if (value === null || value === undefined) return value;
  if (language === "en") return String(value).replace(/_/g, " ");
  let text = String(value).replace(/_/g, " ");
  (REGEX_TRANSLATIONS[language] || []).forEach(([pattern, replacement]) => {
    text = text.replace(pattern, replacement);
  });
  text = applyLiteralReplacements(text, language);
  return localizeBusinessTerms(text, language);
}

function localizeImpact(value, language, t) {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "high") return t.high;
  if (normalized === "medium") return t.medium;
  if (normalized === "low") return t.low;
  return localizeGeneratedText(value || "", language);
}

function localizeChartText(value, language) {
  if (!value || language === "en") return value;
  const text = String(value).replace(/_/g, " ");
  const column = (raw) => localizeColumnLabel(raw, language);

  if (language === "hi") {
    return text
      .replace(/^(.+) distribution$/i, (_, name) => `${column(name)} का वितरण`)
      .replace(/^(.+) spread and outliers$/i, (_, name) => `${column(name)} का फैलाव और आउटलायर`)
      .replace(/^(.+) vs (.+)$/i, (_, y, x) => `${column(y)} बनाम ${column(x)}`)
      .replace(/^Top values for (.+)$/i, (_, name) => `${column(name)} के शीर्ष वैल्यू`)
      .replace(/^Category share for (.+)$/i, (_, name) => `${column(name)} की कैटेगरी हिस्सेदारी`)
      .replace(/^(.+) over time$/i, (_, name) => `समय के साथ ${column(name)}`)
      .replace(/^(.+) trend by row$/i, (_, name) => `पंक्ति के अनुसार ${column(name)} ट्रेंड`)
      .replace(/^Numeric correlation heatmap$/i, "न्यूमेरिक सह-संबंध हीटमैप")
      .replace(/^Distribution of (.+)$/i, (_, name) => `${column(name)} का वितरण`)
      .replace(/^count$/i, "गिनती")
      .replace(/^row$/i, "पंक्ति")
      .replace(/^correlation$/i, "सह-संबंध");
  }

  return text
    .replace(/^(.+) distribution$/i, (_, name) => `${column(name)} distribution`)
    .replace(/^(.+) spread and outliers$/i, (_, name) => `${column(name)} spread aur outliers`)
    .replace(/^(.+) vs (.+)$/i, (_, y, x) => `${column(y)} vs ${column(x)}`)
    .replace(/^Top values for (.+)$/i, (_, name) => `${column(name)} ke top values`)
    .replace(/^Category share for (.+)$/i, (_, name) => `${column(name)} category share`)
    .replace(/^(.+) over time$/i, (_, name) => `${column(name)} over time`)
    .replace(/^(.+) trend by row$/i, (_, name) => `${column(name)} row-wise trend`)
    .replace(/^Numeric correlation heatmap$/i, "Numeric correlation heatmap")
    .replace(/^Distribution of (.+)$/i, (_, name) => `${column(name)} distribution`);
}

function App() {
  const { language, setLanguage, headers: languageHeaders } = useLanguage();
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [mode, setMode] = useState("business");
  const [chartFilter, setChartFilter] = useState("all");
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaChart, setQaChart] = useState(null);
  const [qaLoading, setQaLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState("overview");
  const [historySearch, setHistorySearch] = useState("");
  const [reportGenerating, setReportGenerating] = useState(false);
  const [cleaningData, setCleaningData] = useState(false);
  const [downloadingCleaned, setDownloadingCleaned] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [billingInterval, setBillingInterval] = useState("monthly");
  const [toast, setToast] = useState("");
  const [cleaningSummary, setCleaningSummary] = useState(null);
  const [advisorReport, setAdvisorReport] = useState(null);
  const [loadingAdvisor, setLoadingAdvisor] = useState(false);
  const [activeAction, setActiveAction] = useState("");
  const [restoringData, setRestoringData] = useState(false);
  const [selectedRecommendationIndex, setSelectedRecommendationIndex] = useState(0);
  const [activeRecommendationDetail, setActiveRecommendationDetail] = useState(null);
  const [selectedImplementation, setSelectedImplementation] = useState(null);
  const [activeModal, setActiveModal] = useState(null);
  const implementationGuide = selectedImplementation;
  const [implementationPlans, setImplementationPlans] = useState(() => {
    try {
      return JSON.parse(window.localStorage.getItem("dataMantriImplementationPlans") || "{}") || {};
    } catch {
      return {};
    }
  });
  const [selectedKpi, setSelectedKpi] = useState(null);
  const [historyMeta, setHistoryMeta] = useState(() => {
    try {
      return JSON.parse(window.localStorage.getItem("dataMantriHistoryMeta") || "{}") || {};
    } catch {
      return {};
    }
  });
  const [historySort, setHistorySort] = useState("pinned");
  const [editingHistoryId, setEditingHistoryId] = useState(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [undoHistoryItem, setUndoHistoryItem] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const previousPlanRef = useRef(null);
  const advisorResultRef = useRef(null);
  const modalTriggerRef = useRef(null);
  const restoreAttemptedRef = useRef(false);

  const t = useMemo(() => getTranslations(language), [language]);
  const display = useCallback((value) => localizeGeneratedText(value, language), [language]);
  const displayLabel = useCallback((value) => localizeColumnLabel(value, language), [language]);
  const displayImpact = useCallback((value) => localizeImpact(value, language, t), [language, t]);
  const authHeaders = useMemo(() => ({
    ...languageHeaders,
    Authorization: `Bearer ${token}`,
  }), [languageHeaders, token]);
  const compactTextKey = useCallback((value) => String(value || "")
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .replace(/\b(review|monitor|track|consider|recommended|recommendation|action|business|impact|insight|finding|dataset|data)\b/g, "")
    .replace(/\s+/g, " ")
    .trim(), []);
  const truncateSentence = useCallback((value, max = 150) => {
    const text = String(value || "").trim();
    if (text.length <= max) return text;
    const clipped = text.slice(0, max).replace(/\s+\S*$/, "");
    return `${clipped}...`;
  }, []);
  const formatBusinessValue = useCallback((value, options = {}) => {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "string" && /[a-zA-Z]/.test(value) && !/^[₹$]?\s*[\d,.\s]+%?$/.test(value)) return value;
    const raw = typeof value === "number" ? value : Number(String(value).replace(/[₹$,%\s,]/g, ""));
    if (!Number.isFinite(raw)) return String(value);
    const source = String(value);
    const prefix = options.currency || (source.includes("₹") ? "₹" : source.includes("$") ? "$" : "");
    const suffix = options.percent || source.includes("%") ? "%" : "";
    const abs = Math.abs(raw);
    const digits = abs >= 1000000000 ? `${(raw / 1000000000).toFixed(abs >= 10000000000 ? 1 : 2)}B`
      : abs >= 1000000 ? `${(raw / 1000000).toFixed(abs >= 10000000 ? 1 : 2)}M`
      : Math.round(raw).toLocaleString();
    return `${prefix}${digits}${suffix}`;
  }, []);
  const handleDrag = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    if (event.type === "dragenter" || event.type === "dragover") {
      setDragActive(true);
    } else if (event.type === "dragleave") {
      setDragActive(false);
    }
  }, []);
  const handleDrop = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    const droppedFile = event.dataTransfer?.files?.[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError("");
      setStatus("");
    }
  }, []);

  const buildRecommendationDetail = (rec, index = 0) => {
    const impact = rec?.expected_business_impact || {};
    const confidence = getConfidenceMeta(rec || {});
    const title = rec?.title || rec?.action || "Recommended action";
    const roi = rec?.roi || impact.roi || rec?.expected_roi || "Medium";
    const checklist = getRecommendationChecklist(rec);
    const expectedRevenue = rec?.expected_revenue || rec?.estimated_revenue_increase || impact.revenue_increase || "Revenue uplift estimate available after validation.";
    const expectedCost = rec?.expected_cost || rec?.expected_savings || "Cost estimate depends on execution scope.";
    return {
      title,
      rank: getRecommendationRankLabel(rec, index),
      problem: getRecommendationFinding(rec) || "A material business signal needs focused ownership.",
      explanation: getRecommendationWhy(rec) || getRecommendationDetail(rec) || "This recommendation is based on the strongest decision signal available in the uploaded analysis.",
      evidence: rec?.evidence_summary || rec?.evidence?.map((item) => Object.values(item).filter(Boolean).join(": ")).join(" | ") || rec?.supporting_evidence?.join?.(", ") || "Dataset signals, KPI movement, confidence level, and business impact were used.",
      impact: rec?.business_impact || rec?.expected_impact || rec?.impact || "Medium business impact",
      roi,
      expectedRevenue,
      expectedCost,
      timeline: rec?.implementation_time || impact.implementation_time || "2-4 weeks",
      difficulty: rec?.implementation_difficulty || impact.difficulty || "Medium",
      owner: rec?.owner || "Business lead",
      confidence,
      confidenceSummary: rec?.confidence_summary || display(`${confidence.label} confidence is based on the dataset signal strength, input quality, and operational relevance.`),
      kpisAffected: rec?.kpis_affected || rec?.related_kpis || rec?.source_columns || rec?.contributing_features || [],
      checklist,
      dependencies: rec?.dependencies || rec?.required_resources || [],
      risks: rec?.potential_risks || rec?.risks || ["Operational adoption may be slower than expected", "External demand may change during rollout"],
      successMetrics: rec?.success_metrics || ["ROI lift", "Revenue movement", "Execution completion", "Risk reduction"],
      relatedKpis: rec?.related_kpis || rec?.kpis_affected || rec?.source_columns || [],
      priority: getRecommendationImpact(rec),
      implementation: getRecommendedImplementation(rec),
    };
  };

  const closeModal = useCallback(() => {
    setActiveModal(null);
    setActiveRecommendationDetail(null);
    setSelectedKpi(null);
    setSelectedImplementation(null);
    if (activeModal === "reportPreview") {
      setReportGenerating(false);
    }
  }, [activeModal]);

  const openRecommendationDetails = (rec, index, event) => {
    if (event?.currentTarget) modalTriggerRef.current = event.currentTarget;
    setSelectedRecommendationIndex(index);
    setActiveRecommendationDetail(buildRecommendationDetail(rec, index));
    setActiveModal("recommendationDetails");
  };

  const openImplementationGuide = (rec, index = selectedRecommendationIndex, event) => {
    if (event?.currentTarget) modalTriggerRef.current = event.currentTarget;
    const detail = rec?.rank && rec?.checklist ? rec : buildRecommendationDetail(rec, index);
    setSelectedImplementation(detail);
    setActiveRecommendationDetail(null);
    setActiveModal("implementationGuide");
  };

  const openKpiExplanation = useCallback((kpi, event) => {
    if (event?.currentTarget) modalTriggerRef.current = event.currentTarget;
    setSelectedKpi(kpi);
    setActiveModal("kpiExplanation");
  }, []);

  const openUpgradeModal = useCallback((event) => {
    if (event?.currentTarget) modalTriggerRef.current = event.currentTarget;
    setActiveModal("upgrade");
  }, []);

  const openReportPreview = useCallback((event) => {
    if (event?.currentTarget) modalTriggerRef.current = event.currentTarget;
    setActiveModal("reportPreview");
  }, []);

  const getRecommendationImpact = useCallback((rec) => {
    const rawImpact = rec?.impact || rec?.priority || rec?.business_impact || t.medium;
    const normalized = String(rawImpact || t.medium).toLowerCase();
    if (normalized.includes("high")) return "High";
    if (normalized.includes("low")) return "Low";
    return "Medium";
  }, [t.medium]);
  const getRecommendationClass = useCallback((rec) => getRecommendationImpact(rec).toLowerCase(), [getRecommendationImpact]);
  const getRecommendationDetail = useCallback((rec) => (
    rec?.recommended_action
    || rec?.detail
    || rec?.recommended_action
    || rec?.observation
    || rec?.expected_outcome
    || ""
  ), []);
  const getRecommendationFinding = useCallback((rec) => (
    rec?.business_finding || rec?.reason || rec?.observation || rec?.title || ""
  ), []);
  const getRecommendationWhy = useCallback((rec) => (
    rec?.why_it_matters || rec?.business_impact || rec?.impact || rec?.expected_impact || ""
  ), []);
  const getRecommendationSummary = useCallback((rec) => {
    const summary = rec?.summary || rec?.one_line_summary || getRecommendationFinding(rec) || getRecommendationDetail(rec);
    return truncateSentence(summary || "Focus this action where the business signal is strongest.", 96);
  }, [getRecommendationDetail, getRecommendationFinding, truncateSentence]);
  const getRecommendationRankLabel = useCallback((rec, index) => {
    const text = `${rec?.title || ""} ${rec?.business_impact || ""} ${rec?.impact || ""} ${rec?.roi || ""}`.toLowerCase();
    if (text.includes("roi") || text.includes("profit")) return "Highest ROI";
    if (text.includes("quick") || text.includes("easy") || text.includes("low effort")) return "Quick Win";
    if (text.includes("risk") || text.includes("anomaly") || text.includes("drop")) return "Risk Reduction";
    if (text.includes("cost") || text.includes("saving")) return "Cost Saving";
    if (text.includes("growth") || text.includes("revenue") || text.includes("expand")) return "Growth Opportunity";
    return index === 0 ? "Leadership Priority" : index === 1 ? "Quick Win" : "Long-Term Strategy";
  }, []);
  const getRecommendedImplementation = useCallback((rec) => {
    const action = getRecommendationDetail(rec);
    const titleKey = compactTextKey(rec?.title);
    const actionKey = compactTextKey(action);
    if (actionKey && actionKey !== titleKey) return action;
    const timeline = rec?.implementation_time || rec?.expected_business_impact?.implementation_time || "2-4 weeks";
    const difficulty = rec?.implementation_difficulty || rec?.expected_business_impact?.difficulty || "Medium";
    return display(`Assign an owner, define the affected segment, launch the first intervention, and measure lift within ${timeline}. Difficulty: ${difficulty}.`);
  }, [compactTextKey, display, getRecommendationDetail]);
  const getRecommendationChecklist = useCallback((rec) => {
    const explicit = rec?.implementation_checklist || rec?.checklist || rec?.steps;
    if (Array.isArray(explicit) && explicit.length) return explicit;
    const action = getRecommendationDetail(rec);
    return [
      display("Confirm the affected segment and baseline KPI."),
      display(action || "Define the first business intervention and expected outcome."),
      display("Assign an owner and weekly decision cadence."),
      display("Launch a controlled pilot before scaling spend or process changes."),
      display("Measure ROI, adoption, and risk reduction after the first cycle."),
    ];
  }, [display, getRecommendationDetail]);
  const getUniqueRecommendations = useCallback((items = []) => {
    const seen = new Set();
    return (items || []).filter((rec) => {
      const key = compactTextKey(`${rec?.title || ""} ${getRecommendationFinding(rec) || ""} ${getRecommendationDetail(rec) || ""}`).slice(0, 120);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [compactTextKey, getRecommendationDetail, getRecommendationFinding]);
  const textRepeats = useCallback((primary, secondary) => {
    const primaryKey = compactTextKey(primary);
    const secondaryKey = compactTextKey(secondary);
    if (!primaryKey || !secondaryKey) return false;
    return primaryKey === secondaryKey || primaryKey.includes(secondaryKey) || secondaryKey.includes(primaryKey);
  }, [compactTextKey]);
  const getUniqueInsights = useCallback((items = [], recommendations = []) => {
    const seen = new Set(recommendations.map((rec) => compactTextKey(`${rec?.title || ""} ${getRecommendationFinding(rec) || ""}`)));
    return (items || []).filter((insight) => {
      const key = compactTextKey(`${insight?.title || ""} ${insight?.detail || ""}`).slice(0, 120);
      if (!key) return false;
      const duplicatedByRecommendation = Array.from(seen).some((recKey) => recKey && (recKey.includes(key) || key.includes(recKey)));
      if (duplicatedByRecommendation || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [compactTextKey, getRecommendationFinding]);
  const getConfidenceMeta = useCallback((item) => {
    const conf = item?.ai_confidence?.percent ?? item?.confidence_score ?? item?.confidence ?? 0;
    const percent = Number(conf <= 1 ? conf * 100 : conf) || 0;
    const label = item?.ai_confidence?.label || (percent >= 80 ? "High" : percent >= 60 ? "Medium" : "Low");
    return { label, percent: Math.round(percent), className: label.toLowerCase() };
  }, []);
  const getConfidenceLabel = useCallback((item) => {
    const meta = getConfidenceMeta(item);
    return `${meta.label} ${meta.percent}%`;
  }, [getConfidenceMeta]);
  const ConfidenceBadge = ({ item }) => {
    const meta = getConfidenceMeta(item);
    return (
      <span
        className={`confidence-badge ${meta.className}`}
        title={display("This score represents how confident the AI is in the generated insight based on the available data.")}
      >
        <span>{display("AI Confidence")}</span>
        <strong>{display(`${meta.label} Confidence`)}</strong>
        <em>{meta.percent}%</em>
      </span>
    );
  };
  const DatasetConfidenceCard = ({ confidence }) => {
    const meta = getConfidenceMeta({ confidence });
    return (
      <div className="metric-card small dataset-confidence-card">
        <span>{display("AI Confidence")}</span>
        <strong>{meta.percent}%</strong>
        <small>{display(`${meta.label} Confidence`)}</small>
      </div>
    );
  };

  useEffect(() => {
    if (advisorReport && advisorResultRef.current) {
      advisorResultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [advisorReport]);

  const pages = [
    { key: "overview", label: t.overview },
    { key: "visualizations", label: t.visualizations },
    { key: "ask", label: t.ask },
    { key: "history", label: t.history },
    { key: "profile", label: t.profile },
  ];

  const modeLabel = mode === "eli5"
    ? (language === "hi" ? "आसान" : language === "hinglish" ? "Simple" : "ELI5")
    : mode === "business"
    ? (language === "hi" ? "बिजनेस" : language === "hinglish" ? "Business" : "Business")
    : (language === "hi" ? "डेटा" : "Data");
  const modeSummary = mode === "eli5"
    ? t.modeSummaryEli5
    : mode === "business"
    ? t.modeSummaryBusiness
    : t.modeSummaryData;

  const modeInsights = (insight) => {
    const localizedMode = insight.modes_i18n?.[mode]?.[language] || insight.modes?.[mode];
    if (localizedMode) return display(localizedMode);
    const detail = display(insight.detail || "");
    if (mode === "eli5") {
      const themes = [
        "Think of a kitchen preparing dinner: if one ingredient runs short, the whole meal changes.",
        "Think of checking the weather before leaving home: the signal helps you plan early.",
        "Think of a family budget: the biggest expense or income source deserves attention first.",
        "Think of a busy restaurant: a sudden rush tells the owner to adjust stock and staff.",
        "Think of school marks: one weak subject can pull down the final report card.",
        "Think of traffic: a sudden jam tells you where the route needs fixing.",
      ];
      const theme = themes[Math.abs(String(insight.title || detail).length + (insight.evidence?.length || 0)) % themes.length];
      return `${t.inShort} ${theme} ${detail.split(". ")[0]}.`;
    }
    if (mode === "business") {
      const businessText = insight.business_observation || insight.business_explanation || detail.replace(/\b(Random Forest|Isolation Forest|KMeans|SHAP|correlation|statistical|model|algorithm)\b/gi, "analysis");
      return `${businessText.replace(/\s+/g, " ").trim()} ${businessText.length < 150 ? "Use it to protect margin, prioritize growth, or reduce operating risk." : ""}`.trim();
    }

    const evidence = insight.evidence?.length ? ` Evidence points: ${insight.evidence.length}.` : "";
    return `${detail}${evidence} Confidence: ${Math.round((insight.confidence || 0.65) * 100)}%. Model reasoning includes correlation checks, distribution shape, anomaly pressure, forecast direction, and available feature importance. Assumption: uploaded records represent the current operating pattern.`;
  };

  const fetchProfile = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/profile`, {
        headers: authHeaders,
      });
      setProfile(response.data);
      setHistory(response.data.history || []);
      const savedLanguage = response.data.preferred_language;
      if (LANGUAGE_SEQUENCE.includes(savedLanguage) && savedLanguage !== language) {
        setLanguage(savedLanguage);
      }
    } catch (err) {
      console.error(err);
      if (err.response?.status === 401) {
        handleLogout();
      }
    }
  }, [authHeaders, language, setLanguage]);

  const restoreLatestDataset = useCallback(async (requestedLanguage = language, force = false) => {
    if (force) {
      restoreAttemptedRef.current = false;
    }
    if (!token || restoreAttemptedRef.current) return;
    restoreAttemptedRef.current = true;
    setRestoringData(true);
    try {
      const response = await axios.get(`${API_BASE}/api/restore/latest-dataset`, {
        params: { language: requestedLanguage },
        headers: {
          ...authHeaders,
          ...getLanguageHeaders(requestedLanguage),
        },
      });
      if (response.data?.has_dataset && response.data.dataset?.analysis) {
        const restored = {
          filename: response.data.dataset.filename,
          upload_id: response.data.dataset.upload_id,
          dataset_lifecycle: response.data.dataset.dataset_lifecycle,
          ...response.data.dataset.analysis,
        };
        setData(restored);
        setCleaningSummary(restored.cleaning_summary || null);
        setStatus("");
      } else {
        setData(null);
        setCleaningSummary(null);
      }
    } catch (err) {
      console.error("Could not restore latest dataset", err);
    } finally {
      setRestoringData(false);
    }
  }, [authHeaders, language, token]);

  const handleLanguageChange = useCallback(async (nextLanguage) => {
    if (!LANGUAGE_SEQUENCE.includes(nextLanguage)) return;
    const normalizedLanguage = setLanguage(nextLanguage);
    if (token) {
      try {
        await axios.post(
          `${API_BASE}/api/language/user`,
          { language: normalizedLanguage },
          {
            headers: {
              ...authHeaders,
              ...getLanguageHeaders(normalizedLanguage),
            },
          }
        );
        setProfile((current) => current ? { ...current, preferred_language: normalizedLanguage } : current);
      } catch (err) {
        console.error("Could not persist language preference", err);
      }
      await restoreLatestDataset(normalizedLanguage, true);
    }
  }, [authHeaders, restoreLatestDataset, setLanguage, token]);

  const getHealthScore = () => {
    if (!data) return null;
    const missing = Object.values(data.data_quality?.missing_percent || {}).reduce((acc, val) => acc + val, 0);
    const duplicate = data.data_quality?.duplicate_percent || 0;
    return Math.max(20, Math.round(100 - Math.min(80, missing + duplicate)));
  };

  const hasDataset = Boolean(data && (data.dataset_lifecycle || data.profile || data.validation_report));

  const getDatasetLifecycle = () => {
    if (!hasDataset) return null;
    const lifecycle = data.dataset_lifecycle || {};
    const validation = data.validation_report || {};
    const domain = data.domain_detection || {};
    const health = data.dataset_health || data.data_quality?.health_engine || {};
    return {
      name: lifecycle.current_dataset || data.original_filename || data.filename || "Selected dataset",
      uploadTime: lifecycle.upload_time || data.created_at || null,
      analysisTime: lifecycle.analysis_time || null,
      rows: lifecycle.rows ?? validation.row_count ?? data.profile?.shape?.rows ?? 0,
      columns: lifecycle.columns ?? validation.column_count ?? data.profile?.shape?.columns ?? 0,
      domain: lifecycle.domain || domain.domain || "custom",
      confidence: lifecycle.domain_confidence ?? domain.confidence ?? 0,
      healthScore: lifecycle.dataset_health ?? health.overall_health_score ?? getHealthScore(),
      status: lifecycle.status || data.analysis_status || "complete",
      models: lifecycle.models_used || data.models_used || [],
    };
  };

  const getTopCategory = () => {
    const categories = data?.profile?.category_summary || {};
    const topCategoryEntry = Object.entries(categories).sort((a, b) => (b[1]?.top_share || 0) - (a[1]?.top_share || 0))[0];
    return topCategoryEntry?.[1]?.top_value || "—";
  };

  // Rendering helper for KPI values coming from backend.
  // Rules:
  // - If `value` is falsy -> return "N/A".
  // - If `value` is a primitive (string/number) -> return it.
  // - If `value` is an object and has `display_value` -> return that.
  // - Else if it has `raw_value` -> return that.
  // - Otherwise return "N/A" (do not stringify full objects).
  const getKpiDisplayValue = (value) => {
    if (value === null || value === undefined) return "—";
    if (typeof value === "string" || typeof value === "number") return formatBusinessValue(value);
    if (typeof value === "object") {
      if (value.display_value !== undefined && value.display_value !== null) return formatBusinessValue(value.display_value);
      if (value.displayValue !== undefined && value.displayValue !== null) return formatBusinessValue(value.displayValue);
      if (value.raw_value !== undefined && value.raw_value !== null) return formatBusinessValue(value.raw_value);
      if (value.rawValue !== undefined && value.rawValue !== null) return formatBusinessValue(value.rawValue);
      return "—";
    }
    return String(value);
  };

  const getKpiTrendItems = () => {
    if (!hasDataset) return [];
    if (Array.isArray(data.business_kpis) && data.business_kpis.length > 0) {
      return data.business_kpis.map((kpi) => ({
        label: displayLabel(kpi.name),
        value: getKpiDisplayValue(kpi.value),
        percent: Number(kpi.trend) || 0,
        direction: kpi.trend_direction,
        type: "metric",
        icon: kpi.trend_direction === "up" ? "📈" : kpi.trend_direction === "down" ? "📉" : "📊",
        forecast: kpi.forecast,
        previous: kpi.previous_period_comparison,
        impact: kpi.business_impact,
        confidence: kpi.ai_confidence || { label: getConfidenceLabel(kpi), percent: kpi.confidence },
        recommendedAction: kpi.recommended_action,
        sourceColumns: kpi.source_columns || kpi.contributing_features || [],
        positiveDrivers: kpi.positive_drivers || [],
        isGood: kpi.is_good,
        shouldAct: kpi.should_act,
        aiExplanation: kpi.ai_explanation || kpi.why_generated,
        businessExplanation: kpi.business_explanation || kpi.business_impact,
      }));
    }

    if (!data?.kpis) return [];

    // prefer additive discovered_kpis when available (flat mapping)
    const discovered = data.kpis?.discovered_kpis;
    if (discovered && typeof discovered === "object" && Object.keys(discovered).length > 0) {
      return Object.entries(discovered).map(([key, value]) => ({
        label: displayLabel(key),
        value: getKpiDisplayValue(value),
        percent: Number(value?.trend) || 0,
        direction: value?.trend_direction,
        type: "metric",
        icon: value?.trend_direction === "up" ? "📈" : value?.trend_direction === "down" ? "📉" : "📊",
        previous: value?.previous_period_comparison || value?.previous,
        forecast: value?.forecast,
        impact: value?.business_impact,
        confidence: value?.ai_confidence || { label: getConfidenceLabel(value), percent: value?.confidence },
        recommendedAction: value?.recommended_action,
        sourceColumns: value?.source_columns || value?.contributing_features || [],
      }));
    }

    // fallback to legacy kpis object
    return Object.entries(data.kpis).map(([key, value]) => {
      // trend-style KPI from older API shape
      if (value && typeof value === "object" && value.direction && value.label) {
        return {
          label: displayLabel(key),
          value: getKpiDisplayValue(value.label),
          direction: value.direction,
          percent: value.percent,
          type: "trend",
          icon: value.percent >= 0 ? "📈" : "📉",
        };
      }

      // new KPI engine returns structured objects for many KPI cards.
      // Prefer explicit display/raw fields when present to avoid '[object Object]'.
      const displayVal = getKpiDisplayValue(value);
      return {
        label: displayLabel(key),
        value: displayVal,
        type: "metric",
        icon: "📊",
        sourceColumns: [key],
      };
    });
  };

  // Map KPI label -> compact advanced insights (trends/correlations/anomalies)
  const getAdvancedForLabel = (label) => {
    if (!data?.kpis?.discovery_metadata?.advanced_insights) return null;
    const meta = data.kpis.discovery_metadata.advanced_insights || {};
    // Normalize label to possible column key: strip trailing tags like ' Trend (...)', ' Total', ' Sum', ' Average'
    let base = String(label || "");
    const tIdx = base.indexOf(" Trend");
    if (tIdx > -1) base = base.substring(0, tIdx);
    base = base.replace(/\s+(Total|Sum|Average|Avg|Mean)$/i, "").trim();

    const trend = meta.trends && (meta.trends[base] || meta.trends[base.toLowerCase()] || meta.trends[base.toUpperCase()]);
    const correlations = meta.correlations || [];
    const anomalies = meta.anomalies || [];
    return { trend, correlations, anomalies };
  };

  const renderAdvancedForLabel = (label) => {
    const adv = getAdvancedForLabel(label);
    if (!adv) return null;
    return (
      <div className="kpi-advanced" style={{ marginTop: 6 }}>
        {adv.trend && adv.trend.slope_per_day !== undefined && (
          <small className="kpi-trend-snippet" style={{ color: '#334155' }}>
            {adv.trend.slope_per_day > 0 ? '▲' : '▼'} {Number(adv.trend.slope_per_day).toFixed(2)}/day • R² {adv.trend.r2 ?? '—'}
          </small>
        )}
      </div>
    );
  };

  const getStorySummary = () => {
    if (!hasDataset) return t.initialStory;
    const categories = data.profile?.category_summary || {};
    const topCategoryEntry = Object.entries(categories).sort((a, b) => (b[1]?.top_share || 0) - (a[1]?.top_share || 0))[0];
    const topCategory = topCategoryEntry?.[1]?.top_value;
    const topShare = topCategoryEntry?.[1]?.top_share;
    const quality = getHealthScore();
    const concentration = topCategory
      ? language === "hi"
        ? `${topCategory} वर्तमान व्यापार का मुख्य चालक है, जो लगभग ${topShare}% भागीदार है।`
        : language === "hinglish"
        ? `${topCategory} current business ka main driver hai, jo lagbhag ${topShare}% part leta hai.`
        : `${topCategory} is the primary business driver, accounting for about ${topShare}% of the measured activity.`
      : t.noDominantCategory;
    const qualityPhrase = language === "hi"
      ? `डेटा स्वास्थ्य ${quality}/100 है, जो निर्णय लेने के लिए ${quality >= 85 ? "मजबूत" : quality >= 65 ? "ठीक" : "जोखिम भरा"} है।`
      : language === "hinglish"
      ? `Data health ${quality}/100 hai, jo decision-making ke liye ${quality >= 85 ? "strong" : quality >= 65 ? "usable" : "risk-prone"} hai.`
      : `Data health is ${quality}/100, which is ${quality >= 85 ? "strong enough for confident decisions" : quality >= 65 ? "usable with review" : "a risk that should be fixed before major strategy moves"}.`;
    const baseSummary = language === "hi"
      ? `${concentration} ${qualityPhrase}`
      : language === "hinglish"
      ? `${concentration} ${qualityPhrase}`
      : `${concentration} ${qualityPhrase}`;
    if (mode === "eli5") {
      return language === "hi"
        ? `${baseSummary} आसान भाषा में, यह बताता है कि सबसे बड़ा बिजनेस अवसर क्या है और किस हिस्से पर पहले ध्यान देना चाहिए।`
        : language === "hinglish"
        ? `${baseSummary} Simple words mein, ye batata hai sabse bada business opportunity kya hai aur kahan focus karna chahiye.`
        : `${baseSummary} In plain terms, this explains the leading business opportunity and the first area the leadership should address.`;
    }
    if (mode === "data") {
      return language === "hi"
        ? `${baseSummary} एनालिस्ट नोट: प्रमुख KPI, ट्रेंड दिशा और डेटा गुणवत्ता पर ध्यान दें.`
        : language === "hinglish"
        ? `${baseSummary} Analyst note: key KPI, trend direction aur data quality pe dhyan do.`
        : `${baseSummary} Analyst note: focus on the leading KPI, trend direction, and the current quality signals before deeper modeling or forecasting.`;
    }
    const businessTakeaway = language === "hi"
      ? `नेतृत्व को इस मुख्य अवसर को तेज़ी से समर्थन देना चाहिए, जबकि जोखिम वाले सेकेंडरी सेगमेंट पर नियंत्रण बनाए रखा जाए।`
      : language === "hinglish"
      ? `Leadership ko is main opportunity pe fast support dena chahiye, jabki risk wale secondary segment ko control me rakho.`
      : `Leadership should prioritize the leading opportunity while keeping secondary risk areas under close review.`;
    return `${baseSummary} ${businessTakeaway}`;
  };

  const getExecutiveDashboard = () => {
    if (!hasDataset) return {};
    const source = data?.executive_dashboard || {};
    const topRecommendation = visibleRecommendations[0] || {};
    const topRisk = anomalyItems.find((item) => item.severity === "negative") || {};
    const topOpportunity = data.opportunities?.[0] || visibleRecommendations.find((rec) => getRecommendationClass(rec) === "high") || topRecommendation;
    const confidence = getConfidenceMeta({ confidence: datasetLifecycle?.confidence || topRecommendation.confidence || 0.72 });
    const actions = [
      topRecommendation.title || topRecommendation.recommended_action,
      topOpportunity.title || topOpportunity.action,
      topRisk.action || topRisk.title,
      ...(data.business_advice || []),
    ].filter(Boolean);
    const uniqueActions = [];
    actions.forEach((action) => {
      if (!uniqueActions.some((existing) => textRepeats(existing, action))) uniqueActions.push(action);
    });
    const health = healthScore >= 85 ? "Healthy and decision-ready" : healthScore >= 65 ? "Stable with control gaps" : "Needs management attention";
    const opportunity = source.top_opportunity || topOpportunity.title || "Convert the strongest signal into a focused growth initiative";
    const risk = source.top_risk || topRisk.title || data.risks?.[0]?.title || "No material risk is dominating the current view";
    return {
      business_health: source.business_health || health,
      overall_score: source.overall_score ?? Math.round(healthScore ?? 0),
      current_trend: source.current_trend || (getKpiTrendItems().some((item) => item.direction === "up") ? "Positive momentum" : "Stable"),
      top_opportunity: opportunity,
      top_risk: risk,
      expected_revenue_growth: source.expected_revenue_growth || topRecommendation.estimated_revenue_increase || topRecommendation.expected_business_impact?.revenue_increase || "Moderate upside",
      overall_ai_confidence: source.overall_ai_confidence || `${confidence.label} ${confidence.percent}%`,
      immediate_actions: (source.immediate_actions?.length ? source.immediate_actions : uniqueActions).slice(0, 3),
      ceo_takeaway: source.ceo_takeaway || `The business is ${String(health).toLowerCase()}; the next best move is to act on ${String(opportunity).toLowerCase()} while keeping ${String(risk).toLowerCase()} under control.`,
      paragraph: source.paragraph || data.executive_summary || "Data Mantri found a manageable business position with a clear next action, visible risk controls, and enough confidence to move from analysis to execution.",
    };
  };

  const getAnomalyItems = () => {
    if (!hasDataset) return [];
    if (Array.isArray(data.anomaly_engine) && data.anomaly_engine.length) {
      const seen = new Set();
      return data.anomaly_engine.filter((item) => {
        const key = compactTextKey(item.business_headline || item.headline || item.column || item.type);
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      }).slice(0, 3).map((item) => ({
        raw: item,
        title: display(item.business_headline || item.headline || `${displayLabel(item.column || item.contributing_features?.[0] || "Business metric")} needs attention`),
        description: display(item.business_explanation || item.explanation || `${displayLabel(item.column || "This metric")} moved outside its normal operating range, which may signal demand, pricing, supply, or process pressure.`),
        cause: item.possible_cause,
        action: item.suggested_action || item.recommended_action,
        impact: item.business_impact,
        evidence: item.evidence,
        loss: item.estimated_loss,
        opportunity: item.estimated_opportunity,
        timeline: item.timeline,
        severity: String(item.severity || "medium").toLowerCase().includes("high") ? "negative" : "positive",
      }));
    }
    const anomalies = [];
    Object.entries(data.kpis).forEach(([key, value]) => {
      if (value && typeof value === "object" && typeof value.percent === "number") {
        if (value.percent >= 35) {
          const labelText = getKpiDisplayValue(value.label);
          anomalies.push({
            title: displayLabel(key),
            description: language === "hi"
              ? `${labelText} — मजबूत बढ़त दिख रही है.`
              : language === "hinglish"
              ? `${labelText} — strong upward momentum dikh raha hai.`
              : `${labelText} — strong upward momentum detected.`,
            severity: "positive",
          });
        }
        if (value.percent <= -35) {
          const labelText = getKpiDisplayValue(value.label);
          anomalies.push({
            title: displayLabel(key),
            description: language === "hi"
              ? `${labelText} — हाल के डेटा में तेज गिरावट दिख रही है.`
              : language === "hinglish"
              ? `${labelText} — recent data mein steep drop dikh raha hai.`
              : `${labelText} — a steep drop is visible in recent data.`,
            severity: "negative",
          });
        }
      }
    });
    return anomalies.slice(0, 3);
  };

  const getForecastSummary = () => {
    if (!data?.forecasts?.length) {
      return display("Forecast unavailable. Reason: This dataset doesn't contain enough date-based history. Upload invoices, sales history or daily transactions to unlock forecasting.");
    }
    return t.forecastGenerated(data.forecasts.length);
  };

  const getForecastMeta = () => {
    const forecasts = data?.forecasts || [];
    const first = forecasts[0] || {};
    const points = first.y || first.values || first.forecast || first.predictions || [];
    const numericPoints = Array.isArray(points)
      ? points.map((point) => Number(point?.y ?? point?.value ?? point)).filter(Number.isFinite).slice(-8)
      : [];
    const start = numericPoints[0] ?? 0;
    const end = numericPoints[numericPoints.length - 1] ?? start;
    const direction = end > start ? "Upward" : end < start ? "Downward" : "Stable";
    const confidence = first.confidence || first.ai_confidence || (numericPoints.length >= 4 ? 0.74 : 0.58);
    return {
      points: numericPoints.length ? numericPoints : [42, 48, 46, 54, 58, 62],
      direction,
      confidence,
      trend: first.trend || first.expected_trend || `${direction} trend expected`,
      explanation: first.business_explanation || first.explanation || "Forecast confidence improves when the dataset contains consistent time-based business activity. Use this signal for demand, staffing, inventory, and revenue planning.",
      assumptions: first.assumptions || ["Recent patterns continue", "No major market shock", "Uploaded history reflects current operations"],
    };
  };

  const getInsightPriority = (confidence) => {
    if (confidence >= 0.8) return t.high;
    if (confidence >= 0.55) return t.medium;
    return t.low;
  };

  const getInsightPriorityClass = (confidence) => {
    if (confidence >= 0.8) return "high";
    if (confidence >= 0.55) return "medium";
    return "low";
  };
  const getInsightTypeLabel = (insight) => {
    const text = `${insight?.icon || ""} ${insight?.title || ""} ${insight?.impact || ""}`.toLowerCase();
    if (text.includes("profit") || text.includes("margin")) return "💰 Profit Driver";
    if (text.includes("inventory") || text.includes("stock")) return "📦 Inventory Alert";
    if (text.includes("customer")) return "👥 Customer Trend";
    if (text.includes("product") || text.includes("rating")) return "⭐ Product Opportunity";
    if (text.includes("risk") || text.includes("drop") || text.includes("anomaly") || text.includes("alert")) return "⚠ Revenue Risk";
    if (text.includes("growth") || text.includes("opportunity") || text.includes("revenue")) return "📈 Growth Opportunity";
    return "🎯 Strategic Recommendation";
  };

  const PremiumBadge = () => <span className="premium-badge">🔒 {t.premiumFeature}</span>;

  const PremiumLockedPreview = ({ title, description, children }) => (
    <div className="premium-lock-preview">
      <div className="premium-preview-content" aria-hidden="true">
        {children}
      </div>
      <div className="premium-lock-overlay">
        <PremiumBadge />
        <h3>{title}</h3>
        <p>{description}</p>
        <button className="primary-btn" onClick={(event) => openUpgradeModal(event)}>{t.upgradeToPremium}</button>
      </div>
    </div>
  );

  const showToast = useCallback((message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  }, []);

  const loadRazorpayCheckout = () =>
    new Promise((resolve, reject) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }

      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => reject(new Error("Could not load Razorpay Checkout."));
      document.body.appendChild(script);
    });

  const missingPercent = data ? Object.values(data.data_quality.missing_percent || {}).reduce((acc, val) => acc + val, 0) : 0;
  const duplicatePercent = data?.data_quality?.duplicate_percent ?? 0;
  const cleanPercent = data ? Math.max(0, 100 - duplicatePercent - missingPercent) : 0;
  const qualityPercent = data ? Math.max(0, Math.min(100, 100 - duplicatePercent - missingPercent)) : 0;
  const chartTextColor = darkMode ? "#f8fafc" : "#0f172a";
  const localizeChartObject = useCallback((chartSource) => {
    const parsed = typeof chartSource === "string" ? JSON.parse(chartSource) : chartSource;
    const chart = JSON.parse(JSON.stringify(parsed || {}));
    const translateTitle = (title) => {
      if (!title) return title;
      if (typeof title === "string") return { text: localizeChartText(title, language) };
      return { ...title, text: localizeChartText(title.text, language) };
    };

    chart.layout = chart.layout || {};
    chart.layout.title = translateTitle(chart.layout.title);
    ["xaxis", "yaxis"].forEach((axis) => {
      if (!chart.layout[axis]) chart.layout[axis] = {};
      if (chart.layout[axis].title) {
        chart.layout[axis].title = translateTitle(chart.layout[axis].title);
      } else if (chart.layout[axis].title?.text) {
        chart.layout[axis].title.text = localizeChartText(chart.layout[axis].title.text, language);
      }
    });
    if (chart.layout.coloraxis?.colorbar?.title) {
      chart.layout.coloraxis.colorbar.title = translateTitle(chart.layout.coloraxis.colorbar.title);
    }
    chart.data = (chart.data || []).map((trace) => ({
      ...trace,
      name: localizeChartText(trace.name, language),
      hovertemplate: localizeGeneratedText(trace.hovertemplate || "", language) || trace.hovertemplate,
    }));
    return chart;
  }, [language]);

  const userName = profile?.email
    ? profile.email
        .split("@")[0]
        .replace(/[^a-zA-Z0-9 ]/g, " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase())
    : "Data Manager";
  const plan = (profile?.plan || "basic").toLowerCase();
  const hasFullAccess = profile?.has_full_access ?? plan === "premium";
  const isPremium = true;
  const isUnlimited = hasFullAccess;
  const userPlan = plan === "trial" ? t.trialPlan : plan === "premium" ? t.premiumPlan : t.basicPlan;
  const userInitial = userName.charAt(0) || "D";
  const usageFor = (feature) => profile?.usage?.[feature] || profile?.limits?.[feature] || null;
  const chatbotUsage = usageFor("chatbot_query");
  const basicQueryLimit = chatbotUsage?.limit ?? 4;
  const basicQueriesUsed = chatbotUsage?.used ?? profile?.total_queries ?? 0;
  const formatApiError = (err, fallback) => {
    if (err?.error) return err.error;
    const detail = err.response?.data?.detail;
    const envelopeError = err.response?.data?.error;
    if (envelopeError) return err.response?.data?.details ? `${envelopeError}: ${err.response.data.details}` : envelopeError;
    if (detail?.message) return detail.message;
    if (typeof detail === "string") return detail;
    return fallback;
  };
  const normalizeUploadResponse = (payload) => {
    if (!payload) {
      return { success: false, error: t.uploadFailed, details: "Empty response from upload API." };
    }
    if (payload.success === false) {
      return { success: false, error: payload.error || t.uploadFailed, details: payload.details || "" };
    }
    const analysisPayload = payload.analysis || payload.data;
    if (payload.success === true && analysisPayload) {
      return {
        success: true,
        data: {
          filename: payload.filename,
          dataset_id: payload.dataset_id,
          upload_id: payload.upload_id ?? payload.dataset_id,
          ...analysisPayload,
        },
      };
    }
    if (payload.profile && payload.kpis) {
      return { success: true, data: payload };
    }
    return { success: false, error: t.uploadFailed, details: "Upload API response did not include analysis." };
  };
  const usageCards = ["csv_upload", "chatbot_query", "voice_advisor", "report_download"]
    .map((feature) => ({ key: feature, ...(usageFor(feature) || {}) }))
    .filter((item) => item.label);
  const planCountdown = plan === "trial" && profile?.trial_days_remaining != null
    ? t.trialEndsIn(profile.trial_days_remaining)
    : plan === "premium" && profile?.subscription_days_remaining != null
    ? t.premiumRenewsIn(profile.subscription_days_remaining)
    : "";

  useEffect(() => {
    document.body.classList.toggle("dark-mode", darkMode);
    if (token) {
      fetchProfile();
    }
  }, [darkMode, token, fetchProfile]);

  useEffect(() => {
    if (token && !data && !restoreAttemptedRef.current) {
      restoreLatestDataset();
    }
  }, [token, data, restoreLatestDataset]);

  useEffect(() => {
    localStorage.setItem("language", language);
    document.documentElement.lang = language === "hi" ? "hi" : language === "hinglish" ? "hi-IN" : "en";
    document.documentElement.dir = "ltr";
  }, [language]);

  useEffect(() => {
    if (!profile?.email) return;

    const previousPlan = previousPlanRef.current;
    if (!previousPlan && plan === "trial") {
      const trialToastKey = `trial-started-${profile.email}`;
      if (!localStorage.getItem(trialToastKey)) {
        showToast(t.trialStarted);
        localStorage.setItem(trialToastKey, "true");
      }
    }

    if (previousPlan === "trial" && plan === "basic") {
      showToast(t.trialExpired);
    }

    previousPlanRef.current = plan;
  }, [plan, profile?.email, showToast, t.trialExpired, t.trialStarted]);

  useEffect(() => {
    window.localStorage.setItem("dataMantriImplementationPlans", JSON.stringify(implementationPlans));
  }, [implementationPlans]);

  useEffect(() => {
    window.localStorage.setItem("dataMantriHistoryMeta", JSON.stringify(historyMeta));
  }, [historyMeta]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError("");
    setStatus("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setError("");
    setActiveAction("analyze");
    setLoading(true);
    setStatus(t.statusAnalyzing);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: authHeaders,
      });
      const normalized = normalizeUploadResponse(response.data);
      if (!normalized.success) {
        throw normalized;
      }

      setData(normalized.data);
      setStatus(t.statusComplete);
      showToast(t.statusComplete);
      await fetchProfile();
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, t.uploadFailed));
      setStatus("");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setData(null);
    setProfile(null);
    setHistory([]);
    setStatus("");
    setError("");
    restoreAttemptedRef.current = false;
  };

  const exportCSV = () => {
    if (!file) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(file);
    a.download = file.name;
    a.click();
  };

  const getHistoryDisplayName = (item) => {
    const meta = historyMeta[item.id || item.upload_id] || {};
    return meta.title || item.original_filename || item.filename || item.summary || "Untitled dataset";
  };

  const togglePinHistoryItem = (historyId) => {
    setHistoryMeta((current) => ({
      ...current,
      [historyId]: {
        ...current[historyId],
        pinned: !current[historyId]?.pinned,
      },
    }));
  };

  const renameHistoryItem = (historyId, title) => {
    setHistoryMeta((current) => ({
      ...current,
      [historyId]: {
        ...current[historyId],
        title: title.trim() ? title : current[historyId]?.title,
      },
    }));
  };

  const deleteHistoryItem = async (historyId) => {
    if (!window.confirm(display("Delete this history item? This will not delete your other reports."))) return;
    const existingItem = history.find((item) => (item.id || item.upload_id) === historyId);
    if (!existingItem) return;
    setUndoHistoryItem(existingItem);
    try {
      await axios.delete(`${API_BASE}/history/${historyId}`, {
        headers: authHeaders,
      });
      setHistory((items) => items.filter((item) => (item.id || item.upload_id) !== historyId));
      if (data?.upload_id === historyId || data?.dataset_id === String(historyId)) {
        setData(null);
        setCleaningSummary(null);
        setAdvisorReport(null);
      }
      await fetchProfile();
      showToast(`${t.historyDeleted} ${display("Undo")}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || t.deleteFailed);
    }
  };

  const undoDeleteHistoryItem = () => {
    if (!undoHistoryItem) return;
    setHistory((current) => [undoHistoryItem, ...current]);
    setUndoHistoryItem(null);
    showToast(display("Restore"));
  };

  const getImplementationPlan = (detail) => {
    if (!detail) return { status: "Not started", owner: "", notes: "", updatedAt: null };
    return implementationPlans[detail.title] || { status: "Not started", owner: "", notes: "", updatedAt: null };
  };

  const saveImplementationPlan = (detail, updates) => {
    if (!detail) return;
    setImplementationPlans((current) => ({
      ...current,
      [detail.title]: {
        ...(current[detail.title] || {}),
        ...updates,
        updatedAt: new Date().toISOString(),
      },
    }));
  };

  const getConfidenceReasons = (item = {}) => {
    const confidence = item.confidence?.percent ?? item.confidence ?? 0;
    const reasons = [];
    if (confidence >= 85) {
      reasons.push(display("Strong historical consistency and clear signal strength."));
    } else if (confidence >= 60) {
      reasons.push(display("Moderate trend stability with enough supporting data."));
    } else if (confidence > 0) {
      reasons.push(display("Emerging signal; validate with the next reporting cycle."));
    }
    if (item.sourceColumns?.length) {
      reasons.push(display(`Driven by ${displayLabel(item.sourceColumns[0])} and core business features.`));
    }
    if (!reasons.length) {
      reasons.push(display("Confidence is based on historical pattern strength, quality, and explanatory feature signals."));
    }
    return reasons;
  };

  const openHistoryDataset = async (historyId) => {
    setRestoringData(true);
    setError("");
    try {
      const response = await axios.get(`${API_BASE}/api/restore/dataset/${historyId}`, {
        params: { language },
        headers: authHeaders,
      });
      if (response.data?.success && response.data.dataset?.analysis) {
        const restored = {
          filename: response.data.dataset.filename,
          upload_id: response.data.dataset.upload_id,
          dataset_lifecycle: response.data.dataset.dataset_lifecycle,
          ...response.data.dataset.analysis,
        };
        setData(restored);
        setCleaningSummary(restored.cleaning_summary || null);
        setAdvisorReport(null);
        setCurrentPage("overview");
        await fetchProfile();
        showToast(display("Dataset loaded."));
      }
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, display("Could not load this dataset.")));
    } finally {
      setRestoringData(false);
    }
  };

  const deleteAllHistory = async () => {
    if (!window.confirm(display("Delete all history? This will remove every saved analysis from your workspace."))) return;
    try {
      await axios.delete(`${API_BASE}/history`, {
        headers: authHeaders,
      });
      setHistory([]);
      setData(null);
      await fetchProfile();
      showToast(t.historyCleared);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || t.deleteFailed);
    }
  };

  const resetAnalysis = () => {
    if (!window.confirm(display("Reset the current analysis? This will clear the dataset and return to upload state. History will remain intact."))) return;
    setData(null);
    setStatus("");
    setError("");
    setLoading(false);
    setCleaningData(false);
    setDownloadingCleaned(false);
    setReportGenerating(false);
    closeModal();
    setCleaningSummary(null);
    setAdvisorReport(null);
    setSelectedKpi(null);
    setActiveRecommendationDetail(null);
    setSelectedImplementation(null);
    setQaQuestion("");
    setQaAnswer("");
    setQaChart(null);
    setActiveAction("");
    setHistorySearch("");
    setEditingHistoryId(null);
    setRenameDraft("");
    setCurrentPage("overview");
    setMode("business");
    setChartFilter("all");
    setSelectedRecommendationIndex(0);
    showToast(display("Analysis reset. Upload a new dataset to start again."));
  };

  const handleAutoCleanData = async () => {
    if (!hasDataset) return;
    setActiveAction("autoClean");
    setCleaningData(true);
    setStatus(t.cleaningData);
    setError("");

    try {
      const response = await axios.post(
        `${API_BASE}/clean-data`,
        {},
        { headers: authHeaders }
      );
      setData(response.data);
      setCleaningSummary(response.data.cleaning_summary || null);
      setStatus(t.cleanedDatasetApplied(response.data.filename));
      showToast(t.cleanedDatasetApplied(response.data.filename));
      await fetchProfile();
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, t.cleanDataFailed));
      if (err.response?.status === 429) openUpgradeModal();
      setStatus("");
    } finally {
      setCleaningData(false);
    }
  };

  const handleDownloadCleanedData = async () => {
    if (!hasDataset) return;
    setActiveAction("downloadCleaned");
    setDownloadingCleaned(true);
    setStatus(t.preparingCleanedDownload);
    try {
      const response = await axios.get(`${API_BASE}/clean-data/download`, {
        headers: authHeaders,
        responseType: "blob",
      });
      const blobUrl = URL.createObjectURL(response.data);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `cleaned_${file?.name || data?.filename || "dataset.csv"}`;
      a.click();
      URL.revokeObjectURL(blobUrl);
      setStatus("");
      showToast(t.downloadCleanedData);
      await fetchProfile();
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, t.cleanDataFailed));
      if (err.response?.status === 429) openUpgradeModal();
      setStatus("");
    } finally {
      setDownloadingCleaned(false);
    }
  };

  const handleUpgradePlan = async () => {
    if (paymentLoading) return;
    setPaymentLoading(true);
    setStatus(t.paymentLoading);
    setError("");
    try {
      await loadRazorpayCheckout();
      const orderResponse = await axios.post(
        `${API_BASE}/create-order`,
        { interval: billingInterval },
        { headers: authHeaders }
      );

      const order = orderResponse.data;
      let checkoutOpened = false;
      const checkout = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: APP_NAME,
        description: "Premium subscription - ₹100/month",
        order_id: order.order_id,
        prefill: { email: profile?.email || "" },
        theme: { color: "#2563eb" },
        handler: async (paymentResponse) => {
          try {
            await axios.post(
              `${API_BASE}/verify-payment`,
              paymentResponse,
              { headers: authHeaders }
            );
            await fetchProfile();
            setStatus(t.upgradeComplete);
            showToast(t.paymentSuccessful);
            closeModal();
          } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || t.upgradeFailed);
            setStatus("");
          } finally {
            setPaymentLoading(false);
          }
        },
        modal: {
          ondismiss: () => {
            checkoutOpened = false;
            setPaymentLoading(false);
            setStatus("");
          },
        },
      });

      checkout.on?.("payment.failed", (response) => {
        setError(response?.error?.description || t.upgradeFailed);
        setStatus("");
        setPaymentLoading(false);
      });

      checkout.open();
      checkoutOpened = true;
      window.setTimeout(() => {
        if (!checkoutOpened) {
          setPaymentLoading(false);
          setStatus("");
        }
      }, 1200);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || t.upgradeFailed);
      setStatus("");
      setPaymentLoading(false);
    }
  };

  const exportDashboardPDF = async () => {
    if (!hasDataset) return;
    setActiveAction("downloadReport");
    setReportGenerating(true);
    openReportPreview();
    try {
      await axios.post(
        `${API_BASE}/generate-report`,
        { language },
        { headers: authHeaders }
      );
      await fetchProfile();
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, t.questionFailed));
      if (err.response?.status === 429) openUpgradeModal();
    }
    setTimeout(() => {
      setReportGenerating(false);
    }, 900);
  };

  const askQuestion = async () => {
    if (!qaQuestion.trim() || !hasDataset) return;
    setQaLoading(true);
    setQaAnswer("");
    setQaChart(null);

    try {
      const response = await axios.post(
        `${API_BASE}/ask`,
        { question: qaQuestion, language },
        { headers: authHeaders }
      );
      setQaAnswer(response.data.answer);
      setQaChart(response.data.chart || null);
      await fetchProfile();
    } catch (err) {
      console.error(err);
      setQaAnswer(formatApiError(err, t.questionFailed));
      if ([403, 429].includes(err.response?.status)) {
        openUpgradeModal();
      }
    } finally {
      setQaLoading(false);
    }
  };

  const handleBusinessAdvisor = async () => {
    if (!hasDataset) return;
    setLoadingAdvisor(true);
    setError("");
    setActiveAction("businessAdvisor");

    try {
      const response = await axios.post(
        `${API_BASE}/business-advisor`,
        { language },
        { headers: authHeaders }
      );
      const advisoryData = response.data.advisory || response.data;
      setAdvisorReport(advisoryData);
      showToast(display("Business Advisor report is ready. Scroll down to view it."));
    } catch (err) {
      console.error(err);
      setError(display(err.response?.data?.message || "Failed to generate Business Advisor report"));
    } finally {
      setLoadingAdvisor(false);
    }
  };

  const sortedHistory = [...history].sort((a, b) => {
    const aMeta = historyMeta[a.id || a.upload_id] || {};
    const bMeta = historyMeta[b.id || b.upload_id] || {};
    if (aMeta.pinned && !bMeta.pinned) return -1;
    if (!aMeta.pinned && bMeta.pinned) return 1;
    if (historySort === "oldest") {
      return new Date(a.created_at) - new Date(b.created_at);
    }
    return new Date(b.created_at) - new Date(a.created_at);
  });

  const filteredHistory = sortedHistory.filter((item) =>
    String(item.filename || item.original_filename || "").toLowerCase().includes(historySearch.toLowerCase()) ||
    String(item.summary || "").toLowerCase().includes(historySearch.toLowerCase())
  );

  const normalizedFilter = chartFilter.toLowerCase();
  const filteredCharts = hasDataset
    ? [
        ...(data.charts || []).filter(
          (chart) =>
            normalizedFilter === "all" ||
            chart.type?.toLowerCase() === normalizedFilter ||
            chart.type?.toLowerCase().includes(normalizedFilter)
        ),
        ...((normalizedFilter === "all" || normalizedFilter === "forecast")
          ? (data.forecasts || [])
          : []),
      ]
    : [];

  const visibleCharts = hasDataset ? (filteredCharts.length ? filteredCharts : [...(data.charts || []), ...(data.forecasts || [])]) : [];
  const showFilterFallback = hasDataset && filteredCharts.length === 0 && (data.charts || []).length > 0;
  const chartCountMessage = hasDataset
    ? t.showingCharts(visibleCharts.length, (data.charts?.length || 0) + (data.forecasts?.length || 0))
    : "";

  const healthScore = getHealthScore();
  const storySummary = getStorySummary();
  const anomalyItems = getAnomalyItems();
  const advisorSummaryText = advisorReport?.advisory_summary || advisorReport?.summary || "";
  const advisorTopActions = advisorReport?.top_actions?.length
    ? advisorReport.top_actions
    : advisorReport?.recommendations?.slice(0, 3).map((rec, index) => ({
        rank: index + 1,
        action: rec.title,
        impact: getRecommendationImpact(rec),
        detail: getRecommendationDetail(rec),
      })) || [];
  const forecastSummary = getForecastSummary();
  const forecastMeta = getForecastMeta();
  const datasetLifecycle = getDatasetLifecycle();
  const visibleRecommendations = getUniqueRecommendations(data?.recommendations || []);
  const technicalModelList = ["Isolation Forest", "Local Outlier Factor", "KMeans", "Random Forest", "SHAP", "Prophet", "LightGBM", "XGBoost"];
  const visibleInsights = getUniqueInsights(data?.insights || [], visibleRecommendations);
  const executiveDashboard = getExecutiveDashboard();
  const selectedRecommendation = visibleRecommendations[selectedRecommendationIndex] || visibleRecommendations[0] || null;
  const datasetPipelineItems = [
    "Data Profiled",
    "Data Cleaned",
    "Domain Detected",
    "KPI Discovery Completed",
    "Forecast Analysis Completed",
    "Anomaly Detection Completed",
    "Business Recommendation Engine Completed",
    "Explainable AI Completed",
    "Executive Summary Generated",
  ];

  useEffect(() => {
    if (selectedRecommendationIndex >= visibleRecommendations.length) {
      setSelectedRecommendationIndex(0);
    }
  }, [selectedRecommendationIndex, visibleRecommendations.length]);

  if (!token) {
    return <Auth setToken={setToken} />;
  }

  const activeModalConfig = (() => {
    if (activeModal === "recommendationDetails" && activeRecommendationDetail) {
      const activePlan = getImplementationPlan(activeRecommendationDetail);
      return {
        title: display("Recommendation details"),
        className: "recommendation-detail-panel",
        overlayClassName: "recommendation-detail-portal",
        content: (
          <>
            <div className="recommendation-dialog-header">
              <div className="recommendation-dialog-title">
                <span className={`priority-pill ${String(activeRecommendationDetail.priority || "").toLowerCase()}`}>
                  {displayImpact(activeRecommendationDetail.priority)}
                </span>
                <div>
                  <span className="eyebrow">{display(activeRecommendationDetail.rank)}</span>
                  <h3>{display(activeRecommendationDetail.title)}</h3>
                </div>
              </div>
              <button className="ghost-btn dialog-close-btn" type="button" onClick={closeModal}>{display("Close")}</button>
            </div>
            <div className="recommendation-dialog-body">
              <div className="detail-metric-grid">
                <span>{display("Expected ROI")}<strong>{display(activeRecommendationDetail.roi)}</strong></span>
                <span>{display("Timeline")}<strong>{display(activeRecommendationDetail.timeline)}</strong></span>
                <span>{display("Difficulty")}<strong>{display(activeRecommendationDetail.difficulty)}</strong></span>
                <span>{display("Owner")}<strong>{display(activeRecommendationDetail.owner)}</strong></span>
              </div>
              <div className="detail-section">
                <h4>{display("Business problem")}</h4>
                <p>{display(activeRecommendationDetail.problem)}</p>
              </div>
              <div className="detail-section">
                <h4>{display("AI reasoning")}</h4>
                <p>{display(activeRecommendationDetail.explanation)}</p>
              </div>
              <div className="detail-section">
                <h4>{display("Evidence")}</h4>
                <p>{display(activeRecommendationDetail.evidence)}</p>
              </div>
              <div className="detail-two-col">
                <div className="detail-section">
                  <h4>{display("Expected revenue")}</h4>
                  <p>{display(activeRecommendationDetail.expectedRevenue)}</p>
                </div>
                <div className="detail-section">
                  <h4>{display("Expected cost")}</h4>
                  <p>{display(activeRecommendationDetail.expectedCost)}</p>
                </div>
              </div>
              <div className="detail-section">
                <h4>{display("Implementation checklist")}</h4>
                <ul>
                  {activeRecommendationDetail.checklist.map((item, index) => <li key={index}>{display(item)}</li>)}
                </ul>
              </div>
              <div className="detail-two-col">
                <div className="detail-section">
                  <h4>{display("Potential risks")}</h4>
                  <ul>{activeRecommendationDetail.risks.map((item, index) => <li key={index}>{display(item)}</li>)}</ul>
                </div>
                <div className="detail-section">
                  <h4>{display("Success metrics")}</h4>
                  <ul>{activeRecommendationDetail.successMetrics.map((item, index) => <li key={index}>{display(item)}</li>)}</ul>
                </div>
              </div>
              <div className="detail-two-col">
                <div className="detail-section">
                  <h4>{display("Dependencies")}</h4>
                  <ul>
                    {(activeRecommendationDetail.dependencies.length ? activeRecommendationDetail.dependencies : [display("Owner alignment"), display("KPI baseline"), display("Execution capacity")]).map((item, index) => <li key={index}>{display(item)}</li>)}
                  </ul>
                </div>
                <div className="detail-section">
                  <h4>{display("Notes")}</h4>
                  <p>{display(activeRecommendationDetail.confidenceSummary)}</p>
                </div>
              </div>
              <div className="detail-chip-row">
                {(activeRecommendationDetail.kpisAffected.length ? activeRecommendationDetail.kpisAffected : activeRecommendationDetail.relatedKpis).slice(0, 5).map((item, index) => (
                  <span key={index}>{displayLabel(item)}</span>
                ))}
              </div>
              <div className="detail-status-row">
                <span>{display("Implementation status")}: <strong>{display(activePlan.status)}</strong></span>
                <span>{display("Owner")}: <strong>{display(activePlan.owner || activeRecommendationDetail.owner)}</strong></span>
              </div>
            </div>
            <div className="recommendation-dialog-footer detail-actions">
              <button className="primary-btn" type="button" onClick={() => openImplementationGuide(selectedRecommendation, selectedRecommendationIndex)}>{display("Implement")}</button>
              <button className="secondary-btn" type="button" onClick={() => showToast(display("Recommendation marked complete."))}>{display("Mark Complete")}</button>
              <button className="ghost-btn" type="button" disabled title={display("PDF export requires backend report generation support.")}>{display("Export PDF")}</button>
              <button className="ghost-btn" type="button" disabled title={display("Task creation requires an integrated task system.")}>{display("Create Task")}</button>
            </div>
          </>
        ),
      };
    }

    if (activeModal === "implementationGuide" && implementationGuide) {
      const plan = getImplementationPlan(implementationGuide);
      const statusOptions = ["Not started", "In progress", "Completed", "Blocked"];
      return {
        title: display("Implementation Guide"),
        className: "insight-drawer implementation-drawer",
        content: (
          <>
            <div className="drawer-header">
              <div>
                <span className="eyebrow">{display("Implementation Guide")}</span>
                <h3>{display(implementationGuide.title)}</h3>
              </div>
              <button className="ghost-btn" type="button" onClick={closeModal}>{display("Close")}</button>
            </div>
            <div className="detail-metric-grid">
              <span>{display("Priority")}<strong>{display(implementationGuide.priority)}</strong></span>
              <span>{display("Expected ROI")}<strong>{display(implementationGuide.roi)}</strong></span>
              <span>{display("Status")}<strong>{display(plan.status)}</strong></span>
              <span>{display("Timeline")}<strong>{display(implementationGuide.timeline)}</strong></span>
            </div>
            <div className="detail-section">
              <h4>{display("Business objective")}</h4>
              <p>{display(implementationGuide.implementation)}</p>
            </div>
            <div className="detail-section">
              <h4>{display("Recommended actions")}</h4>
              <ul>{implementationGuide.checklist.map((item, index) => <li key={index}>{display(item)}</li>)}</ul>
            </div>
            <div className="detail-two-col">
              <div className="detail-section">
                <h4>{display("KPIs to monitor")}</h4>
                <ul>{(implementationGuide.kpisAffected.length ? implementationGuide.kpisAffected : implementationGuide.successMetrics).slice(0, 4).map((item, index) => <li key={index}>{displayLabel(item)}</li>)}</ul>
              </div>
              <div className="detail-section">
                <h4>{display("Success criteria")}</h4>
                <ul>{implementationGuide.successMetrics.map((item, index) => <li key={index}>{display(item)}</li>)}</ul>
              </div>
            </div>
            <div className="detail-grid">
              <div className="detail-section">
                <h4>{display("Update status")}</h4>
                <select
                  value={plan.status}
                  onChange={(event) => saveImplementationPlan(implementationGuide, { status: event.target.value })}
                  aria-label={display("Implementation status")}
                >
                  {statusOptions.map((option) => (
                    <option key={option} value={option}>{display(option)}</option>
                  ))}
                </select>
              </div>
              <div className="detail-section">
                <h4>{display("Owner")}</h4>
                <input
                  type="text"
                  value={plan.owner}
                  onChange={(event) => saveImplementationPlan(implementationGuide, { owner: event.target.value })}
                  placeholder={display("Assign a team owner")}
                  aria-label={display("Implementation owner")}
                />
              </div>
            </div>
            <div className="detail-section">
              <h4>{display("Execution notes")}</h4>
              <textarea
                value={plan.notes}
                onChange={(event) => saveImplementationPlan(implementationGuide, { notes: event.target.value })}
                placeholder={display("Add progress notes, blockers, or success observations")}
                rows={4}
                aria-label={display("Implementation notes")}
              />
            </div>
            <div className="detail-actions">
              <button
                className="primary-btn"
                type="button"
                onClick={() => {
                  saveImplementationPlan(implementationGuide, { status: "Completed" });
                  showToast(display("Implementation plan updated."));
                }}
              >
                {display("Mark Completed")}
              </button>
              <button className="ghost-btn" type="button" disabled title={display("PDF export requires backend report generation support.")}>{display("Export as PDF")}</button>
            </div>
          </>
        ),
      };
    }

    if (activeModal === "kpiExplanation" && selectedKpi) {
      const confidenceReasons = getConfidenceReasons(selectedKpi);
      return {
        title: display("KPI explanation"),
        className: "insight-modal",
        content: (
          <>
            <div className="modal-header">
              <div>
                <span className="eyebrow">{display("KPI explanation")}</span>
                <h3>{selectedKpi.label}</h3>
              </div>
              <button className="ghost-btn" type="button" onClick={closeModal}>{display("Close")}</button>
            </div>
            <div className="detail-metric-grid">
              <span>{display("Current Value")}<strong>{selectedKpi.value}</strong></span>
              <span>{display("Trend")}<strong>{selectedKpi.direction === "up" ? display("Up") : selectedKpi.direction === "down" ? display("Down") : display("Stable")}</strong></span>
              <span>{display("Forecast")}<strong>{selectedKpi.forecast !== undefined && selectedKpi.forecast !== null ? formatBusinessValue(selectedKpi.forecast) : "—"}</strong></span>
              <span>{display("Confidence")}<strong>{selectedKpi.confidence?.percent ? `${Math.round(selectedKpi.confidence.percent)}%` : "—"}</strong></span>
            </div>
            <div className="detail-section">
              <h4>{display("AI reasoning")}</h4>
              <p>{display(selectedKpi.aiExplanation || selectedKpi.impact || "The AI identified this signal based on trend direction, stability, and its relationship to the dataset's core business drivers.")}</p>
            </div>
            <div className="detail-section">
              <h4>{display("Business explanation")}</h4>
              <p>{display(selectedKpi.businessExplanation || selectedKpi.impact || "This metric directly influences revenue, margin, or operational efficiency and should be monitored with priority.")}</p>
            </div>
            <div className="detail-section">
              <h4>{display("Confidence explanation")}</h4>
              <ul className="confidence-reasons">
                {confidenceReasons.map((reason, index) => <li key={index}>{display(reason)}</li>)}
              </ul>
            </div>
            <div className="detail-section">
              <h4>{display("Recommended action")}</h4>
              <p>{display(selectedKpi.recommendedAction || "Compare this KPI by segment and prioritize the biggest business driver.")}</p>
            </div>
            <div className="detail-section">
              <h4>{display("Related KPIs")}</h4>
              <div className="detail-chip-row">
                {(selectedKpi.positiveDrivers || selectedKpi.sourceColumns || [selectedKpi.label]).map((item, index) => (
                  <span key={index}>{displayLabel(item)}</span>
                ))}
              </div>
            </div>
          </>
        ),
      };
    }

    if (activeModal === "upgrade") {
      return {
        title: t.upgradeTitle,
        className: "report-modal upgrade-modal",
        content: (
          <div className="premium-modal">
            <div className="premium-top">
              <div className="premium-icon">💎</div>
              <div className="premium-badge-inline"><PremiumBadge /></div>
            </div>

            <h3 className="premium-title">{t.upgradeTitle}</h3>
            <p className="premium-subtitle">{t.upgradeText}</p>

            <div className="premium-features">
              <div className="feature">{display("Unlimited uploads")}</div>
              <div className="feature">{display("Unlimited chatbot")}</div>
              <div className="feature">{display("Unlimited Mitra voice")}</div>
              <div className="feature">{display("Unlimited reports")}</div>
              <div className="feature">{display("Auto cleaning")}</div>
              <div className="feature">{display("Smart forecasting")}</div>
            </div>

            <div className="billing-toggle centered">
              <button className={`pill ${billingInterval === "monthly" ? "active" : ""}`} onClick={() => setBillingInterval("monthly")}>{display("Monthly")}</button>
              <button className={`pill ${billingInterval === "yearly" ? "active" : ""}`} onClick={() => setBillingInterval("yearly")}>{display("Yearly")}</button>
            </div>

            <div className="price-block">
              <div className="price">{billingInterval === "monthly" ? "₹100 / month" : "₹999 / year"}</div>
              <div className="savings">{billingInterval === "yearly" ? "Save 17% yearly" : ""}</div>
            </div>

            <div className="premium-actions">
              <button className="primary-btn upgrade-cta" onClick={handleUpgradePlan} disabled={paymentLoading}>
                {paymentLoading ? t.paymentLoading : t.upgradeToPremium}
              </button>
              <button className="link-btn maybe-later" onClick={closeModal}>{t.maybeLater}</button>
            </div>
          </div>
        ),
      };
    }

    if (activeModal === "reportPreview") {
      return {
        title: reportGenerating ? t.reportGeneratingTitle : t.reportReadyTitle,
        className: "report-modal",
        closeOnOverlay: !reportGenerating,
        content: (
          <>
            <h3>{reportGenerating ? t.reportGeneratingTitle : t.reportReadyTitle}</h3>
            <p>{reportGenerating ? t.reportGeneratingText : t.reportReadyText}</p>
            <div className="report-modal-actions">
              <button
                className="primary-btn"
                disabled={reportGenerating}
                onClick={() => {
                  window.print();
                  closeModal();
                }}
              >
                {reportGenerating ? t.rendering : t.downloadReportShort}
              </button>
              {!reportGenerating && (
                <button className="secondary-btn" onClick={closeModal}>
                  {t.closePreview}
                </button>
              )}
            </div>
          </>
        ),
      };
    }

    return null;
  })();

  return (
    <>
      <div className="navbar">
        <div className="brand">
          <div className="brand-mark">DM</div>
          <div className="brand-copy">
            <h1 className="brand-title">{APP_NAME}</h1>
            <p className="brand-subtitle">{t.appSubtitle}</p>
          </div>
        </div>

        <div className="navbar-actions">
          <span className="navbar-chip">{modeLabel} {t.mode}</span>
          <span className={`plan-badge ${plan}`}>{userPlan}</span>
          {planCountdown && <span className="trial-countdown">{planCountdown}</span>}
          <button
            className="ghost-btn language-toggle"
            onClick={() => {
              const currentIndex = LANGUAGE_SEQUENCE.indexOf(language);
              const nextIndex = (currentIndex + 1) % LANGUAGE_SEQUENCE.length;
              handleLanguageChange(LANGUAGE_SEQUENCE[nextIndex]);
            }}
            aria-label="Change language"
          >
            {LANGUAGE_BUTTON_LABELS[language] || LANGUAGE_BUTTON_LABELS.en}
          </button>
          <button className="ghost-btn" onClick={() => setDarkMode(!darkMode)}>
            {darkMode ? t.lightMode : t.darkMode}
          </button>
          <button className="ghost-btn" onClick={handleLogout}>{t.logout}</button>
        </div>
      </div>

      <div className="container">
        {toast && <div className="app-toast">{toast}</div>}
        {(loading || restoringData) && (
          <div className="loading-overlay">
            <div className="loading-panel">
              <div className="loader-ring" />
              <div>
                <p>{restoringData ? display("Restoring your latest dashboard") : t.analyzingDataset}</p>
                <span>{restoringData ? display("Loading saved dataset, KPIs, charts, and insights.") : t.loadingSummary}</span>
              </div>
            </div>
          </div>
        )}
        <div className="top-grid">
          <div className="hero-card">
            <div>
              <span className="eyebrow">{t.welcome}</span>
              <h2>{t.heroTitle}</h2>
              <p>{t.heroText}</p>
            </div>
            <div className="hero-actions">
              <button className={`primary-btn ${activeAction === "analyze" ? "active" : ""}`} onClick={handleUpload} disabled={!file || loading}>
                {loading ? t.analyzing : t.analyzeDataset}
              </button>
              <button className={`secondary-btn ${activeAction === "downloadReport" ? "active" : ""}`} onClick={exportDashboardPDF} disabled={!hasDataset}>{t.downloadReport}</button>
              <button className="secondary-btn reset-action" onClick={resetAnalysis} disabled={!hasDataset} title={display("Clear the current dataset and return to the upload screen. History stays intact.")}>
                ↻ {display("Reset analysis")}
              </button>
              <button className={`secondary-btn ${activeAction === "autoClean" ? "active" : ""}`} onClick={handleAutoCleanData} disabled={!hasDataset || cleaningData}>
                {!isPremium && "🔒 "}{cleaningData ? t.cleaningData : t.autoCleanData}
              </button>
              <button className={`secondary-btn ${activeAction === "downloadCleaned" ? "active" : ""}`} onClick={handleDownloadCleanedData} disabled={!hasDataset || downloadingCleaned}>
                {!isPremium && "🔒 "}{downloadingCleaned ? t.preparingCleanedDownload : t.downloadCleanedData}
              </button>
            </div>
          </div>

          <div className="panel-card">
            <div className="profile-card">
              <div className="profile-avatar">{userInitial}</div>
              <div className="profile-copy">
                <p className="profile-label">{t.signedInAs}</p>
                <h3>{userName}</h3>
                <span className={`profile-pill plan-${plan}`}>{userPlan} {t.plan}</span>
              </div>
            </div>

            <div className="panel-row">
              <div>
                <h3>{t.workspaceOverview}</h3>
                <p>{profile?.email || t.loadingProfile}</p>
              </div>
            </div>

            <div className="panel-grid">
              <div className="metric-card small">
                <span>{t.uploads}</span>
                <strong>{profile?.total_uploads ?? 0}</strong>
              </div>
              <div className="metric-card small">
                <span>{t.latestKpis}</span>
                <strong>{hasDataset ? (data.business_kpis?.length || Object.keys(data.kpis?.discovered_kpis || data.kpis || {}).length) : 0}</strong>
              </div>
              <div className="metric-card small">
                <span>{t.qualityScore}</span>
                <strong>{hasDataset ? `${Math.round(datasetLifecycle?.healthScore ?? getHealthScore() ?? 0)}%` : "—"}</strong>
              </div>
            </div>

            <div className="pill-row">
              <button className={`pill ${mode === "business" ? "active" : ""}`} onClick={() => setMode("business")}>{t.businessMode}</button>
              <button className={`pill ${mode === "data" ? "active" : ""}`} onClick={() => setMode("data")}>{t.dataMode}</button>
              <button className={`pill ${mode === "eli5" ? "active" : ""}`} onClick={() => setMode("eli5")}>{t.eli5Mode}</button>
            </div>
          </div>
        </div>

        {!!usageCards.length && (
          <div className="usage-strip">
            <div>
              <span className="eyebrow">{display("Usage")}</span>
              <h3>{display(isUnlimited ? "Premium workspace: unlimited usage" : "Free plan usage limits")}</h3>
            </div>
            <div className="usage-strip-grid">
              {usageCards.map((item) => (
                <div className="usage-mini-card" key={item.key}>
                  <span>{display(item.label)}</span>
                  <strong>{item.unlimited ? display("Unlimited") : `${item.remaining}/${item.limit} ${display("left")}`}</strong>
                  {!item.unlimited && <small>{item.used}/{item.limit} {display("used")} · {display(item.period)}</small>}
                </div>
              ))}
            </div>
            {!isUnlimited && (
              <button className="secondary-btn" onClick={(event) => openUpgradeModal(event)}>
                {display("Unlock unlimited")}
              </button>
            )}
          </div>
        )}

        {advisorReport && (
          <div className="advisor-summary-card" ref={advisorResultRef}>
            <div className="advisor-summary-header">
              <div>
                <h3>{t.businessAdvisor} {display("report")}</h3>
                <p>{display("Your free advisor has reviewed your data and created clear recommendations below.")}</p>
              </div>
            </div>
            {advisorSummaryText && (
              <div className="advisor-summary-text">
                {advisorSummaryText.split("\n").map((line, idx) => (
                  <p key={idx}>{display(line)}</p>
                ))}
              </div>
            )}
            <div className="advisor-cards">
              <div className="advisor-card">
                <h4>{display("Top Actions")}</h4>
                <ul>
                  {advisorTopActions?.map((action, index) => (
                    <li key={index}>
                      <strong>{action.rank}. {display(action.action)}</strong>
                      <p>{display(action.detail)}</p>
                    </li>
                  ))}
                  {!advisorTopActions?.length && <li>{display("No prioritized actions available yet.")}</li>}
                </ul>
              </div>
              <div className="advisor-card">
                <h4>{t.recommendations}</h4>
                <ul>
                  {advisorReport.recommendations?.slice(0, 6).map((rec, index) => (
                    <li key={index}>
                      <strong>{display(rec.title || rec.action || "Recommended action")}</strong>
                      <p>{display(getRecommendationDetail(rec))}</p>
                    </li>
                  ))}
                  {!advisorReport.recommendations?.length && <li>{display("No recommendations available yet.")}</li>}
                </ul>
              </div>
            </div>
            {advisorReport.insights?.length > 0 && (
              <div className="advisor-card advisor-card-insights">
                <h4>{display("Insights")}</h4>
                <ul>
                  {advisorReport.insights.slice(0, 5).map((insight, index) => (
                    <li key={index}>
                      <strong>{display(insight.title)}</strong>
                      <p>{display(insight.detail)}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="advisor-summary-actions">
              <button className="secondary-btn" onClick={() => setAdvisorReport(null)}>{display("Hide report")}</button>
            </div>
          </div>
        )}

        <div
          className={`upload-box ${dragActive ? "drag-active" : ""}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          aria-label="Drag and drop your dataset here"
        >
          <div className="upload-header">
            <div>
              <h3>{t.uploadCsvTitle}</h3>
              <p>{file ? file.name : t.filePrompt}</p>
            </div>
            <span className="status-text">{status}</span>
          </div>
          <div className="upload-input-row">
            <input type="file" accept=".csv,.xlsx,.xls,.json" onChange={handleFileChange} />
            <button className="secondary-btn" onClick={exportCSV} disabled={!file}>
              {t.exportOriginalCsv}
            </button>
          </div>
          <div className="upload-hint-row">
            <span>Supported formats:</span>
            <strong>CSV, XLSX, JSON</strong>
          </div>
          {file && (
            <div className="upload-selected-file">
              <span>Selected file:</span>
              <strong>{file.name}</strong>
            </div>
          )}
          {error && <div className="upload-error">{display(error)}</div>}
        </div>

        <div className="page-tabs">
          {pages.map((page) => (
            <button
              key={page.key}
              className={`tab-button ${currentPage === page.key ? "active" : ""}`}
              onClick={() => setCurrentPage(page.key)}
            >
              {page.label}
            </button>
          ))}
          <button
            className={`tab-button advisor-tab ${activeAction === "businessAdvisor" ? "active" : ""}`}
            onClick={handleBusinessAdvisor}
            disabled={!hasDataset || loadingAdvisor}
            title={t.businessAdvisorTooltip}
          >
            {loadingAdvisor ? "⏳" : "💼"} {t.businessAdvisor}
          </button>
        </div>

        {currentPage === "overview" && (
          <>
            {!hasDataset ? (
              <div className="section empty-state-card onboarding-empty">
                <span className="eyebrow">{t.welcome}</span>
                <h2>{t.uploadFirstDataset}</h2>
                <p>{display("Upload your first CSV to unlock AI KPIs, forecasting, recommendations, Business Advisor, and an executive dashboard.")}</p>
                <div className="panel-grid">
                  {["AI KPIs", "Forecasting", "Recommendations", "Business Advisor", "Executive Dashboard"].map((item) => (
                    <div className="metric-card small" key={item}>
                      <span>{display(item)}</span>
                      <strong>{display("Ready")}</strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <>
            <div className="section executive-summary-panel">
              <div className="section-header">
                <div>
                  <h2>{display("Executive Summary")}</h2>
                  <span>{display(executiveDashboard.paragraph)}</span>
                </div>
              </div>
              {executiveDashboard.ceo_takeaway && (
                <div className="ceo-takeaway">
                  <span>{display("CEO Takeaway")}</span>
                  <strong>{display(executiveDashboard.ceo_takeaway)}</strong>
                </div>
              )}
              <div className="executive-grid">
                <div className="metric-card small">
                  <span>{display("Business Health")}</span>
                  <strong>{display(executiveDashboard.business_health || "Stable")}</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Overall Score")}</span>
                  <strong>{executiveDashboard.overall_score ?? Math.round(healthScore ?? 0)}</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Current Trend")}</span>
                  <strong>{display(executiveDashboard.current_trend || "Stable")}</strong>
                </div>
                <div className="metric-card small wide">
                  <span>{display("Top Opportunity")}</span>
                  <strong>{display(executiveDashboard.top_opportunity || data.opportunities?.[0]?.title || "Prioritize the strongest segment")}</strong>
                </div>
                <div className="metric-card small wide">
                  <span>{display("Top Risk")}</span>
                  <strong>{display(executiveDashboard.top_risk || data.risks?.[0]?.title || "No major risk detected")}</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Expected Revenue Growth")}</span>
                  <strong>{display(executiveDashboard.expected_revenue_growth || "Medium")}</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Overall AI Confidence")}</span>
                  <strong>{display(executiveDashboard.overall_ai_confidence || getConfidenceMeta({ confidence: datasetLifecycle?.confidence || 0 }).label)}</strong>
                </div>
              </div>
              <div className="immediate-actions">
                <span>{display("Immediate Actions")}</span>
                {(executiveDashboard.immediate_actions?.length ? executiveDashboard.immediate_actions : data.business_advice || []).slice(0, 3).map((action, index) => (
                  <p key={index}>{display(action)}</p>
                ))}
              </div>
            </div>
            <div className="section dataset-lifecycle-panel">
              <div className="section-header">
                <div>
                  <h2>{display("Current Dataset")}</h2>
                  <span>{datasetLifecycle?.name}</span>
                </div>
                <span className={`status-text status-${String(datasetLifecycle?.status || "complete").toLowerCase()}`}>
                  {display(datasetLifecycle?.status || "complete")}
                </span>
              </div>
              <div className="panel-grid">
                <div className="metric-card small">
                  <span>{t.rows}</span>
                  <strong>{formatBusinessValue(datasetLifecycle?.rows ?? "—")}</strong>
                </div>
                <div className="metric-card small">
                  <span>{t.columns}</span>
                  <strong>{formatBusinessValue(datasetLifecycle?.columns ?? "—")}</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Domain")}</span>
                  <strong>{displayLabel(datasetLifecycle?.domain || "Custom")}</strong>
                </div>
                <DatasetConfidenceCard confidence={datasetLifecycle?.confidence || 0} />
                <div className="metric-card small">
                  <span>{t.qualityScore}</span>
                  <strong>{Math.round(datasetLifecycle?.healthScore ?? 0)}%</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Upload Time")}</span>
                  <strong>{datasetLifecycle?.uploadTime ? new Date(datasetLifecycle.uploadTime).toLocaleString() : "—"}</strong>
                </div>
                <div className="metric-card small">
                  <span>{display("Analysis Time")}</span>
                  <strong>{datasetLifecycle?.analysisTime ? new Date(datasetLifecycle.analysisTime).toLocaleString() : "—"}</strong>
                </div>
                <div className="metric-card small pipeline-card">
                  <span>{display("AI Analysis Pipeline")}</span>
                  <div className="pipeline-list">
                    {datasetPipelineItems.map((item) => (
                      <strong key={item}>{display(`✓ ${item}`)}</strong>
                    ))}
                  </div>
                  <details className="technical-details">
                    <summary>{display("Technical Details")}</summary>
                    <p>{technicalModelList.join(", ")}</p>
                  </details>
                </div>
              </div>
            </div>
            <div className="dashboard-grid">
              <div className="metric-card">
                <h4>{t.dataStory}</h4>
                <p>{storySummary}</p>
              </div>
              <div className="metric-card health-card">
                <div className="health-card-top">
                  <div>
                    <h4>{t.dataHealth}</h4>
                    <p>{t.dataHealthText}</p>
                  </div>
                  <div className="health-ring" style={{ "--health": qualityPercent }}>
                    <strong>{healthScore ?? "—"}</strong>
                    <span>/100</span>
                  </div>
                </div>
                <div className="health-breakdown">
                  <div className="quality-item">
                    <span>{t.missing}</span>
                    <strong>{missingPercent.toFixed(1)}%</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.duplicates}</span>
                    <strong>{duplicatePercent.toFixed(1)}%</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.clean}</span>
                    <strong>{cleanPercent.toFixed(1)}%</strong>
                  </div>
                </div>
              </div>
              {isPremium ? (
                <div className="metric-card forecast-card">
                  <div className="forecast-card-header">
                    <div>
                      <h4>{t.forecastSummaryTitle}</h4>
                      <p>{forecastSummary}</p>
                    </div>
                    <span className={`priority-pill ${forecastMeta.direction === "Downward" ? "medium" : "high"}`}>{display(forecastMeta.direction)}</span>
                  </div>
                  <div className="forecast-bars" aria-label={display("Forecast chart")}>
                    {forecastMeta.points.map((point, index) => {
                      const maxPoint = Math.max(...forecastMeta.points, 1);
                      return <i key={index} style={{ height: `${Math.max(18, (point / maxPoint) * 100)}%` }} />;
                    })}
                  </div>
                  <div className="forecast-facts">
                    <span>{display("Expected trend")}<strong>{display(forecastMeta.trend)}</strong></span>
                    <span>{display("Forecast confidence")}<strong>{getConfidenceMeta({ confidence: forecastMeta.confidence }).percent}%</strong></span>
                    <span>{display("Confidence interval")}<strong>{display("Conservative range")}</strong></span>
                  </div>
                  <details className="why-details compact">
                    <summary>{display("Business explanation")}</summary>
                    <p>{display(forecastMeta.explanation)}</p>
                    <p><strong>{display("Key assumptions")}</strong>{display((forecastMeta.assumptions || []).join(", "))}</p>
                  </details>
                </div>
              ) : (
                <div className="metric-card premium-preview-card">
                  <PremiumBadge />
                  <h4>{t.forecastSummaryTitle}</h4>
                  <p>{t.forecastReady}</p>
                  <button className="secondary-btn" onClick={(event) => openUpgradeModal(event)}>{t.upgradeToPremium}</button>
                </div>
              )}
            </div>

            {cleaningSummary && (
              <div className="section cleaning-report-panel">
                <div className="section-header">
                  <div>
                    <h2>{t.cleaningReport}</h2>
                    <span>{data?.filename}</span>
                  </div>
                </div>
                <div className="cleaning-report-grid">
                  <div className="quality-item">
                    <span>{t.rowsRemoved}</span>
                    <strong>{Math.max(0, (cleaningSummary.rows_before || 0) - (cleaningSummary.rows_after || 0))}</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.missingFilled}</span>
                    <strong>{cleaningSummary.missing_values_filled || 0}</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.columnsStandardized}</span>
                    <strong>{cleaningSummary.columns_renamed || 0}</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.numericConverted}</span>
                    <strong>{cleaningSummary.numeric_columns_converted || 0}</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.datesStandardized}</span>
                    <strong>{cleaningSummary.date_columns_standardized || 0}</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.outliersRemoved}</span>
                    <strong>{cleaningSummary.outliers_removed || 0}</strong>
                  </div>
                  <div className="quality-item">
                    <span>{t.remainingMissing}</span>
                    <strong>{cleaningSummary.missing_values_after || 0}</strong>
                  </div>
                </div>
                {(cleaningSummary.missing_values_after || 0) === 0 && (
                  <p className="cleaning-note">{t.cleaningPerfectNote}</p>
                )}
              </div>
            )}

            {data && isPremium && anomalyItems.length > 0 && (
              <div className="section anomaly-panel">
                <div className="section-header">
                  <h2>⚠️ {t.anomalyDetection}</h2>
                  <span>{t.anomalySubtitle}</span>
                </div>
                <div className="anomaly-grid">
                  {anomalyItems.map((item, index) => (
                    <div className={`anomaly-card ${item.severity}`} key={index}>
                      <h4>{item.title}</h4>
                      <div className="anomaly-section">
                        <span>{display("Business Explanation")}</span>
                        <p>{item.description}</p>
                      </div>
                      {item.cause && (
                        <div className="anomaly-section">
                          <span>{display("Possible Cause")}</span>
                          <p>{display(item.cause)}</p>
                        </div>
                      )}
                      {item.impact && (
                        <div className="anomaly-section">
                          <span>{display("Business Impact")}</span>
                          <p>{display(item.impact)}</p>
                        </div>
                      )}
                      <div className="anomaly-facts">
                        <span>{display("Severity")}<strong>{display(item.severity === "negative" ? "High" : "Medium")}</strong></span>
                        <span>{display("Estimated Loss")}<strong>{display(item.loss || "Medium exposure")}</strong></span>
                        <span>{display("Opportunity")}<strong>{display(item.opportunity || "Improve control")}</strong></span>
                        <span>{display("Timeline")}<strong>{display(item.timeline || "Next 7 days")}</strong></span>
                      </div>
                      {item.evidence?.length > 0 && (
                        <details className="why-details compact">
                          <summary>{display("Evidence")}</summary>
                          <p>{display(item.evidence.map((ev) => Object.values(ev).filter(Boolean).join(": ")).join(" | "))}</p>
                        </details>
                      )}
                      {item.action && <div className="action-callout">{display(item.action)}</div>}
                      <ConfidenceBadge item={item.raw} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data && !isPremium && (
              <div className="section anomaly-panel">
                <PremiumLockedPreview title={t.anomalyDetection} description={t.anomalySubtitle}>
                  <div className="anomaly-grid">
                    {[0, 1, 2].map((item) => (
                      <div className="anomaly-card positive" key={item}>
                        <h4>{display("Revenue momentum")}</h4>
                        <p>{display("Advanced spike and drop detection appears here for Premium workspaces.")}</p>
                      </div>
                    ))}
                  </div>
                </PremiumLockedPreview>
              </div>
            )}

            {data && (
              <div className="section kpi-trends-section">
                <div className="section-header">
                  <h2>📈 {t.kpiTrends}</h2>
                  <span>{t.kpiSubtitle}</span>
                </div>
                <div className="kpi-trends-grid">
                    {getKpiTrendItems().map((item) => (
                    <div className={`kpi-card ${item.type}`} key={item.label}>
                      <div className="kpi-card-top">
                        <span className="kpi-icon">{item.icon}</span>
                        <p className="kpi-label">{item.label.toUpperCase()}</p>
                      </div>
                      <div className="kpi-card-body">
                        <div className="kpi-primary-value">
                          <span>{display("Current Value")}</span>
                          <strong>{item.value}</strong>
                        </div>
                        <div className="kpi-mini-chart" aria-hidden="true">
                          {[0.35, 0.56, 0.48, 0.72, 0.64, 0.86].map((height, sparkIndex) => (
                            <i
                              key={sparkIndex}
                              style={{ height: `${Math.max(18, Math.min(92, height * 100 + (Number(item.percent) || 0) / 4))}%` }}
                            />
                          ))}
                        </div>
                        <span className={`priority-pill ${item.isGood ? "high" : item.shouldAct ? "medium" : "low"}`}>
                          {item.isGood ? display("Healthy") : item.shouldAct ? display("Needs action") : display("Stable")}
                        </span>
                        {item.type === "trend" && (
                          <span className={`trend-indicator ${item.percent >= 0 ? 'positive' : 'negative'}`}>
                            {item.percent >= 0 ? `+${item.percent}%` : `${item.percent}%`}
                          </span>
                        )}
                        {renderAdvancedForLabel(item.label)}
                      </div>
                      <div className="kpi-quick-row">
                        <span>{display("Trend")}: <strong>{item.direction === "up" ? display("Up") : item.direction === "down" ? display("Down") : display("Stable")}</strong></span>
                        {item.confidence?.percent && <span>{display("Confidence")}: <strong>{item.confidence.label} {Math.round(item.confidence.percent)}%</strong></span>}
                      </div>
                      <button className="secondary-btn kpi-explain-btn" type="button" onClick={(event) => openKpiExplanation(item, event)} aria-label={display("Explain why this KPI matters")}>
                        🧠 {display("Explain KPI")}
                        <span className="chevron">→</span>
                      </button>
                      <div className="sparkline">
                        <div className={`sparkline-bar ${item.percent >= 0 ? 'positive' : 'negative'}`} style={{ width: `${Math.min(90, Math.abs(item.percent) + 10)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data ? (
              <div className="section split-section">
                <div className="insight-column">
                  <div className="section-header">
                    <h2>{mode === "business" ? t.businessIntelligence : mode === "data" ? t.dataAnalystInsights : t.explainLikeIm5}</h2>
                    <div className="filter-row">
                      <span>{t.modeLabel}</span>
                      <strong>{modeLabel}</strong>
                    </div>
                  </div>
                  <p className="mode-summary">{modeSummary}</p>
                  <div className="insights-grid">
                    {visibleInsights.map((insight, index) => (
                      <div className="insight-card" key={index}>
                        <div className="insight-card-top">
                          <span className="insight-label">
  {getInsightTypeLabel(insight)}
</span>
                          <span className={`priority-pill ${getInsightPriorityClass(insight.confidence)}`}>{getInsightPriority(insight.confidence)}</span>
                        </div>
                        <div className="insight-copy">
                          <h4>{display(insight.title)}</h4>
                          <p>{modeInsights(insight)}</p>
                        </div>
                        <ConfidenceBadge item={insight} />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="recommendation-panel">
                  {isPremium ? (
                    <>
                      <div className="section-header">
                        <h2>{t.recommendations}</h2>
                        <span>{visibleRecommendations.length} {t.items}</span>
                      </div>
                      <div className="recommendation-list" role="list" aria-label={display("Recommendations")}>
                        {visibleRecommendations.map((rec, index) => {
                          const detail = buildRecommendationDetail(rec, index);
                          const isSelected = index === selectedRecommendationIndex;
                          return (
                            <button
                              className={`recommendation-list-card ${getRecommendationClass(rec)} ${isSelected ? "selected" : ""}`}
                              key={`${detail.title}-${index}`}
                              type="button"
                              onClick={(event) => openRecommendationDetails(rec, index, event)}
                              aria-pressed={isSelected}
                            >
                              <span className="recommendation-card-top">
                                <span className={`priority-pill ${getRecommendationClass(rec)}`}>{displayImpact(getRecommendationImpact(rec))}</span>
                                <strong>{display(detail.rank)}</strong>
                              </span>
                              <span className="recommendation-list-title">{display(detail.title)}</span>
                              <span className="recommendation-list-summary">{display(getRecommendationSummary(rec))}</span>
                              <span className="recommendation-list-meta">
                                <em>{display("Confidence")} {detail.confidence.percent}%</em>
                                <em>{display("ROI")} {display(detail.roi)}</em>
                              </span>
                              <span className="view-details-link">{display("View Details")}</span>
                            </button>
                          );
                        })}
                      </div>
                    </>
                  ) : (
                    <PremiumLockedPreview title={t.recommendations} description={t.upgradeText}>
                      <div className="recommendations-grid">
                        {[0, 1].map((item) => (
                          <div className="recommendation-card high" key={item}>
                            <div>
                              <h4>{display("Prioritized action")}</h4>
                              <p>{display("Premium recommendations preview the next best action for this dataset.")}</p>
                            </div>
                            <span className="impact-tag">{t.high}</span>
                          </div>
                        ))}
                      </div>
                    </PremiumLockedPreview>
                  )}
                  {mode === "data" && (
                    <div className="data-details-panel">
                      <div className="section-header">
                        <h3>{t.technicalSnapshot}</h3>
                        <span>{t.technicalSnapshotText}</span>
                      </div>
                      <div className="panel-grid">
                        <div className="metric-card small">
                          <span>{t.columns}</span>
                          <strong>{data.profile.shape.columns}</strong>
                        </div>
                        <div className="metric-card small">
                          <span>{t.rows}</span>
                          <strong>{data.profile.shape.rows}</strong>
                        </div>
                        <div className="metric-card small">
                          <span>{t.numericAnalytics}</span>
                          <strong>{Object.keys(data.profile.summary_stats || {}).length}</strong>
                        </div>
                        <div className="metric-card small">
                          <span>{t.topCategory}</span>
                          <strong>{getTopCategory()}</strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="section empty-state-card">
                <h2>{t.uploadFirstDataset}</h2>
                <p>{t.uploadFirstDatasetText}</p>
              </div>
            )}
              </>
            )}
          </>
        )}

        {currentPage === "visualizations" && (
          <>
            {hasDataset ? (
              <div className="section chart-panel">
                <div className="section-header">
                  <div>
                    <h2>{t.visualizations}</h2>
                    <p className="chart-status">{chartCountMessage}</p>
                  </div>
                  <div className="chart-filter-row">
                    {CHART_TYPES.map((type) => (
                      <button
                        key={type}
                        className={`pill ${chartFilter === type ? "active" : ""} ${!isPremium && type !== "all" ? "locked" : ""}`}
                        onClick={() => {
                          if (!isPremium && type !== "all") {
                            openUpgradeModal();
                            return;
                          }
                          setChartFilter(type);
                        }}
                      >
                        {!isPremium && type !== "all" ? "🔒 " : ""}{type === "all" ? t.all : localizeChartText(type, language)}
                      </button>
                    ))}
                  </div>
                </div>
                {showFilterFallback && (
                  <div className="filter-warning-card">
                    <strong>{t.noChartsFilter}</strong>
                    <p>{t.filterFallbackText}</p>
                  </div>
                )}
                {visibleCharts.length ? (
                  visibleCharts.map((chartObj, index) => {
                    const chart = localizeChartObject(chartObj.chart);
                    return (
                      <div className="chart-card" key={index}>
                        <Plot
                          data={chart.data}
                          layout={{
                            ...chart.layout,
                            autosize: true,
                            hovermode: "closest",
                            paper_bgcolor: "rgba(0,0,0,0)",
                            plot_bgcolor: "rgba(0,0,0,0)",
                            template: darkMode ? "plotly_dark" : "plotly_white",
                            font: { color: chartTextColor },
                            xaxis: {
                              ...(chart.layout?.xaxis || {}),
                              tickfont: { color: chartTextColor },
                              title: { ...(chart.layout?.xaxis?.title || {}), font: { color: chartTextColor } },
                            },
                            yaxis: {
                              ...(chart.layout?.yaxis || {}),
                              tickfont: { color: chartTextColor },
                              title: { ...(chart.layout?.yaxis?.title || {}), font: { color: chartTextColor } },
                            },
                          }}
                          style={{ width: "100%", minHeight: 420 }}
                        />
                      </div>
                    );
                  })
                ) : (
                  <div className="empty-card">{t.noVisualizations}</div>
                )}
              </div>
            ) : (
              <div className="section empty-state-card">
                <h2>{t.noVisualizationData}</h2>
                <p>{t.noVisualizationDataText}</p>
              </div>
            )}
          </>
        )}

        {currentPage === "ask" && (
          <>
            {hasDataset ? (
              <div className="section ask-data-section">
                <div className="section-header">
                  <div>
                    <h2>🤖 {t.askYourDataTitle}</h2>
                    <span>{t.askSubtitle}</span>
                  </div>
                  <div className="ask-hint">
                    {t.askHint}
                  </div>
                </div>
                  <div className="ask-data-container">
                  {!isUnlimited && (
                    <div className="usage-hint">
                      <span>{t.basicChatUsage(basicQueriesUsed, basicQueryLimit)}</span>
                      <button className="secondary-btn" onClick={(event) => openUpgradeModal(event)}>{t.upgradeToPremium}</button>
                    </div>
                  )}
                  <div className="ask-input-row">
                    <input
                      type="text"
                      className="ask-input"
                      placeholder={t.askPlaceholder}
                      value={qaQuestion}
                      onChange={(e) => setQaQuestion(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && askQuestion()}
                    />
                    <button className="primary-btn" onClick={askQuestion} disabled={qaLoading || !qaQuestion.trim()}>
                      {qaLoading ? t.analyzing : t.askButton}
                    </button>
                  </div>
                  {qaAnswer && (
                    <div className="ask-answer-card">
                      <div className="answer-badge">{t.aiResponse}</div>
                      <p>{display(qaAnswer)}</p>
                    </div>
                  )}
                  {qaChart && (
                    <div className="qa-chart-card">
                      {(() => {
                        const chart = localizeChartObject(qaChart);
                        return (
                      <Plot
                        data={chart.data}
                        layout={{
                          ...chart.layout,
                          autosize: true,
                          hovermode: "closest",
                          paper_bgcolor: "rgba(0,0,0,0)",
                          plot_bgcolor: "rgba(0,0,0,0)",
                          template: darkMode ? "plotly_dark" : "plotly_white",
                          font: { color: chartTextColor },
                          xaxis: {
                            ...(chart.layout?.xaxis || {}),
                            tickfont: { color: chartTextColor },
                            title: { ...(chart.layout?.xaxis?.title || {}), font: { color: chartTextColor } },
                          },
                          yaxis: {
                            ...(chart.layout?.yaxis || {}),
                            tickfont: { color: chartTextColor },
                            title: { ...(chart.layout?.yaxis?.title || {}), font: { color: chartTextColor } },
                          },
                        }}
                        style={{ width: "100%", minHeight: 360 }}
                      />
                        );
                      })()}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="section empty-state-card">
                <h2>{t.askAfterUpload}</h2>
                <p>{t.askAfterUploadText}</p>
              </div>
            )}
          </>
        )}

        {currentPage === "history" && (
          <div className="section history-section">
            <div className="section-header">
              <div>
                <h2>{t.uploadHistory}</h2>
                <span>{filteredHistory.length} {t.records}</span>
              </div>
              <div className="history-tool-row">
                <div className="history-search-row">
                  <input
                    type="text"
                    className="search-input"
                    placeholder={t.historyPlaceholder}
                    value={historySearch}
                    onChange={(e) => setHistorySearch(e.target.value)}
                    aria-label={t.historyPlaceholder}
                  />
                </div>
                <div className="history-actions-row">
                  <button className="ghost-btn" type="button" onClick={() => setHistorySort(historySort === "newest" ? "oldest" : "newest")}>
                    {historySort === "newest" ? display("Sort: Newest") : display("Sort: Oldest")}
                  </button>
                  <button className="secondary-btn" onClick={deleteAllHistory} disabled={!history.length}>
                    {t.deleteAllHistory}
                  </button>
                </div>
              </div>
            </div>
            {filteredHistory.length ? (
              <div className="history-grid">
                {filteredHistory.map((item) => {
                  const itemId = item.id || item.upload_id;
                  const meta = historyMeta[itemId] || {};
                  const isEditing = editingHistoryId === itemId;
                  return (
                    <div className="history-card" key={itemId}>
                      <div className="history-card-body">
                        <div className="history-title-row">
                          {isEditing ? (
                            <input
                              type="text"
                              className="history-rename-input"
                              value={renameDraft}
                              onChange={(e) => setRenameDraft(e.target.value)}
                              onBlur={() => {
                                renameHistoryItem(itemId, renameDraft);
                                setEditingHistoryId(null);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  renameHistoryItem(itemId, renameDraft);
                                  setEditingHistoryId(null);
                                }
                              }}
                              aria-label={display("Rename dataset")}
                              autoFocus
                            />
                          ) : (
                            <strong>{getHistoryDisplayName(item)}</strong>
                          )}
                          <div className="history-title-pill-row">
                            {meta.pinned && <span className="status-pill pinned">{display("Pinned")}</span>}
                            <span className={`status-text status-${String(item.status || "complete").toLowerCase()}`}>{display(item.status || "complete")}</span>
                          </div>
                        </div>
                        <div className="history-meta-row">
                          <span>{display("Domain")}: {displayLabel(item.domain || item.detected_domain || "Custom")}</span>
                          <span>{display("Date")}: {item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}</span>
                        </div>
                        <p>{display(item.summary)}</p>
                      </div>
                      <div className="history-card-actions">
                        <div className="history-card-actions-top">
                          <time>{new Date(item.created_at).toLocaleString()}</time>
                          <button className="secondary-btn" onClick={() => openHistoryDataset(itemId)}>{display("View Report")}</button>
                          <button className="outline-btn" onClick={() => openHistoryDataset(itemId)}>{display("Duplicate Analysis")}</button>
                        </div>
                        <div className="history-card-actions-bottom">
                          <button
                            className="outline-btn"
                            type="button"
                            onClick={() => {
                              setEditingHistoryId(itemId);
                              setRenameDraft(meta.title || item.original_filename || item.filename || "");
                            }}
                          >
                            {display(meta.title ? "Rename" : "Add title")}
                          </button>
                          <button className="outline-btn" type="button" onClick={() => togglePinHistoryItem(itemId)}>
                            {meta.pinned ? display("Unpin") : display("Pin")}
                          </button>
                          <button className="outline-btn" type="button" disabled title={display("Download requires saved report artifact support.")}>{display("Download Report")}</button>
                          <button className="danger-btn" onClick={() => deleteHistoryItem(itemId)}>{t.deleteHistory}</button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-card">{t.noHistory}</div>
            )}
          </div>
        )}

        {currentPage === "profile" && (
          <Profile
            profile={profile}
            history={history}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            mode={mode}
            setMode={setMode}
            handleLogout={handleLogout}
            userName={userName}
            userEmail={profile?.email}
            userPlan={userPlan}
            plan={plan}
            onUpgrade={(event) => openUpgradeModal(event)}
            language={language}
          />
        )}

        {activeModalConfig && (
          <ModalPortal
            open
            onClose={closeModal}
            title={activeModalConfig.title}
            className={activeModalConfig.className}
            overlayClassName={activeModalConfig.overlayClassName}
            closeOnOverlay={activeModalConfig.closeOnOverlay !== false}
          >
            {activeModalConfig.content}
          </ModalPortal>
        )}

        <footer className="app-footer">
          <div>
            <p>{t.footerText}</p>
          </div>
          <div>
            <span>© {new Date().getFullYear()} Data Mantri AI</span>
          </div>
        </footer>
      </div>
      <VoiceAssistantButton
        token={token}
        hasData={Boolean(data)}
        language={language}
        mode={mode}
        showToast={showToast}
      />
    </>
  );
}

export default App;
