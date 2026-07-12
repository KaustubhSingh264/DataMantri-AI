"""
Master Translation Dictionary for Data Mantri
Single source of truth for all UI strings across English, Hindi, and Hinglish
Used by both frontend and backend for consistency
"""

TRANSLATIONS = {
    "en": {
        # Auth
        "auth": {
            "welcome_back": "Welcome Back",
            "login": "Login",
            "signup": "Sign Up",
            "email": "Email",
            "password": "Password",
            "confirm_password": "Confirm Password",
            "create_account": "Create account",
            "forgot_password": "Forgot password?",
            "invalid_credentials": "Invalid credentials",
            "signup_success": "Trial started. Signup complete. Please login.",
            "password_mismatch": "Passwords do not match.",
            "already_have_account": "Already have an account? Login",
            "reset_password": "Reset Password",
            "reset_link_sent": "Password reset link sent to your email.",
            "password_reset_success": "Password reset successful. Please login.",
        },
        
        # Dashboard
        "dashboard": {
            "welcome": "Welcome",
            "overview": "Overview",
            "visualizations": "Visualizations",
            "ask": "Ask your data",
            "history": "History",
            "profile": "Profile",
            "workspace_overview": "Workspace overview",
            "signed_in_as": "Signed in as",
            "uploads": "Uploads",
            "latest_kpis": "Latest KPIs",
            "quality_score": "Quality Score",
        },
        
        # Upload & Analysis
        "upload": {
            "upload_csv_title": "Upload a CSV to get started",
            "file_prompt": "Drag and drop or browse for a file.",
            "analyze_dataset": "Analyze dataset",
            "analyzing": "Analyzing...",
            "upload_success": "Dataset uploaded and analyzed successfully.",
            "upload_failed": "Failed to upload dataset. Please try again.",
            "analyzing_dataset": "Analyzing your dataset",
            "loading_summary": "Generating premium insights, KPIs, and smart recommendations.",
        },
        
        # Data Quality
        "quality": {
            "data_health": "Data health",
            "quality_score": "Quality Score",
            "missing": "Missing",
            "duplicates": "Duplicates",
            "clean": "Clean",
            "data_health_text": "Visual quality score with missing, duplicate, and clean breakdowns.",
            "technical_snapshot": "Technical snapshot",
            "technical_snapshot_text": "Deep data quality and distribution metrics.",
            "columns": "Columns",
            "rows": "Rows",
            "missing_values": "Missing values",
            "duplicate_rows": "Duplicate rows",
            "clean_data": "Clean data",
        },
        
        # Analysis Results
        "analysis": {
            "data_story": "Data story",
            "summary": "Summary",
            "insights": "Insights",
            "key_findings": "Key Findings",
            "top_category": "Top category",
            "export_original_csv": "Export original CSV",
            "download_cleaned_data": "Download cleaned data",
            "auto_clean_data": "Auto-clean data",
            "cleaning_data": "Cleaning data...",
            "cleaned_dataset_applied": "Cleaned dataset applied successfully.",
            "clean_data_failed": "Failed to clean data. Please try again.",
        },
        
        # KPIs & Performance
        "kpi": {
            "kpi_trends": "KPI Trends",
            "kpi_subtitle": "Performance indicators with directional insights",
            "performance_up": "Performance improved",
            "performance_down": "Performance declined",
            "stable": "Stable",
            "trend": "Trend",
            "direction": "Direction",
        },
        
        # Forecasting
        "forecast": {
            "forecast_summary": "Forecast summary",
            "forecast_ready": "Forecast model ready for analysis.",
            "forecast_generated": "Generated {count} forecasts",
            "predictions": "Predictions",
            "confidence": "Confidence",
            "trend_up": "Upward trend detected",
            "trend_down": "Downward trend detected",
            "trend_stable": "Stable trend",
        },
        
        # Anomalies
        "anomaly": {
            "anomaly_detection": "Anomaly detection",
            "anomaly_subtitle": "Spikes and drops highlighted by AI",
            "anomaly_found": "Anomaly detected",
            "spike_detected": "Spike detected",
            "drop_detected": "Drop detected",
        },
        
        # Business Intelligence
        "business": {
            "business_advisor": "Business Advisor",
            "business_advisor_tooltip": "Get free AI-powered business insights, KPIs, and recommendations",
            "executive_summary": "Executive Summary",
            "top_actions": "Top Actions",
            "opportunities": "Opportunities",
            "recommendations": "Recommendations",
            "risks": "Risks",
            "actions_prioritized": "Prioritized actions for maximum impact",
            "impact": "Impact",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
        },
        
        # Modes
        "mode": {
            "mode": "mode",
            "business_mode": "Business mode",
            "data_mode": "Data mode",
            "eli5_mode": "Explain Like I'm 5",
            "mode_summary_business": "Action-ready suggestions, impact metrics and executive narrative.",
            "mode_summary_data": "Technical profiling, distribution patterns, correlation and quality signals.",
            "mode_summary_eli5": "Simple language insights for fast understanding and easy decisions.",
        },
        
        # Visualizations
        "viz": {
            "visualizations": "Visualizations",
            "showing_charts": "Showing {visible} of {total} visualizations",
            "all_charts": "All",
            "no_charts_filter": "No charts found for this filter.",
            "filter_fallback": "Displaying all available visualizations.",
            "no_visualizations": "No visualizations available",
            "no_visualization_data": "No visualization data yet",
            "chart": "Chart",
            "type": "Type",
            "histogram": "Histogram",
            "bar": "Bar",
            "line": "Line",
            "box": "Box",
            "scatter": "Scatter",
            "pie": "Pie",
            "heatmap": "Heatmap",
        },
        
        # Q&A
        "qa": {
            "ask_your_data": "Ask Your Data",
            "ask_subtitle": "Natural language questions about your dataset",
            "ask_hint": "Try questions like 'Which product is least performing?' or 'What is the top category?'",
            "ask_placeholder": "Type your question here...",
            "ask_button": "Ask",
            "ai_response": "AI response",
            "ask_after_upload": "Ask your data once you upload",
            "no_data_for_questions": "Upload a dataset to enable natural language questions.",
            "question_failed": "Could not process your question. Please try again.",
        },
        
        # Plans & Billing
        "billing": {
            "plan": "plan",
            "basic_plan": "Basic",
            "premium_plan": "Premium",
            "trial_plan": "Free Trial",
            "premium_feature": "Premium feature",
            "upgrade_to_premium": "Upgrade to Premium",
            "trial_ends_in": "Trial ends in {days} days",
            "premium_renews_in": "Premium renews in {days} days",
            "trial_started": "Trial started successfully",
            "trial_expired": "Trial has expired",
            "upgrade_complete": "Upgrade successful",
            "upgrade_failed": "Upgrade failed. Please try again.",
        },
        
        # System Messages
        "system": {
            "loading": "Loading...",
            "saving": "Saving...",
            "success": "Success",
            "error": "Error",
            "warning": "Warning",
            "info": "Info",
            "please_try_again": "Please try again.",
            "loading_profile": "Loading profile...",
            "logout": "Logout",
            "light_mode": "Light mode",
            "dark_mode": "Dark mode",
            "language": "Language",
        },
        
        # Error Messages
        "errors": {
            "connection_error": "Connection error. Please check your internet.",
            "server_error": "Server error. Please try again later.",
            "unauthorized": "Unauthorized. Please login again.",
            "invalid_file": "Invalid file format. Please upload a CSV.",
            "file_too_large": "File is too large. Maximum size is 100MB.",
            "no_data": "No data available.",
            "something_went_wrong": "Something went wrong. Please try again.",
        },
    },
    
    "hi": {
        # Auth
        "auth": {
            "welcome_back": "स्वागत है",
            "login": "लॉगिन",
            "signup": "साइन अप करें",
            "email": "ईमेल",
            "password": "पासवर्ड",
            "confirm_password": "पासवर्ड की पुष्टि करें",
            "create_account": "खाता बनाएं",
            "forgot_password": "पासवर्ड भूल गए?",
            "invalid_credentials": "अमान्य साख",
            "signup_success": "ट्रायल शुरू हुआ। साइन अप पूर्ण। कृपया लॉगिन करें।",
            "password_mismatch": "पासवर्ड मेल नहीं खाते।",
            "already_have_account": "पहले से खाता है? लॉगिन करें",
            "reset_password": "पासवर्ड रीसेट करें",
            "reset_link_sent": "पासवर्ड रीसेट लिंक आपके ईमेल पर भेज दिया गया है।",
            "password_reset_success": "पासवर्ड रीसेट सफल। कृपया लॉगिन करें।",
        },
        
        # Dashboard
        "dashboard": {
            "welcome": "स्वागत है",
            "overview": "अवलोकन",
            "visualizations": "दृश्यांकन",
            "ask": "अपने डेटा से पूछें",
            "history": "इतिहास",
            "profile": "प्रोफाइल",
            "workspace_overview": "कार्यक्षेत्र अवलोकन",
            "signed_in_as": "में साइन इन किया गया",
            "uploads": "अपलोड",
            "latest_kpis": "नवीनतम KPIs",
            "quality_score": "गुणवत्ता स्कोर",
        },
        
        # Upload & Analysis
        "upload": {
            "upload_csv_title": "शुरू करने के लिए एक CSV अपलोड करें",
            "file_prompt": "फ़ाइल को खींचें और ड्रॉप करें या ब्राउज़ करें।",
            "analyze_dataset": "डेटासेट का विश्लेषण करें",
            "analyzing": "विश्लेषण जारी है...",
            "upload_success": "डेटासेट सफलतापूर्वक अपलोड और विश्लेषण किया गया।",
            "upload_failed": "डेटासेट अपलोड करने में विफल। कृपया फिर से कोशिश करें।",
            "analyzing_dataset": "आपके डेटासेट का विश्लेषण जारी है",
            "loading_summary": "प्रीमियम अंतर्दृष्टि, KPIs और स्मार्ट सिफारिशें तैयार की जा रही हैं।",
        },
        
        # Data Quality
        "quality": {
            "data_health": "डेटा स्वास्थ्य",
            "quality_score": "गुणवत्ता स्कोर",
            "missing": "अनुपलब्ध",
            "duplicates": "डुप्लिकेट",
            "clean": "स्वच्छ",
            "data_health_text": "लापता, डुप्लिकेट और स्वच्छ डेटा का विज़ुअल गुणवत्ता स्कोर।",
            "technical_snapshot": "तकनीकी स्नैपशॉट",
            "technical_snapshot_text": "गहरा डेटा गुणवत्ता और वितरण मेट्रिक्स।",
            "columns": "स्तंभ",
            "rows": "पंक्तियाँ",
            "missing_values": "अनुपलब्ध मान",
            "duplicate_rows": "डुप्लिकेट पंक्तियाँ",
            "clean_data": "स्वच्छ डेटा",
        },
        
        # Analysis Results
        "analysis": {
            "data_story": "डेटा कहानी",
            "summary": "सारांश",
            "insights": "अंतर्दृष्टि",
            "key_findings": "मुख्य निष्कर्ष",
            "top_category": "शीर्ष श्रेणी",
            "export_original_csv": "मूल CSV निर्यात करें",
            "download_cleaned_data": "स्वच्छ डेटा डाउनलोड करें",
            "auto_clean_data": "डेटा को स्वचालित रूप से साफ करें",
            "cleaning_data": "डेटा साफ किया जा रहा है...",
            "cleaned_dataset_applied": "स्वच्छ डेटासेट सफलतापूर्वक लागू किया गया।",
            "clean_data_failed": "डेटा साफ करने में विफल। कृपया फिर से कोशिश करें।",
        },
        
        # KPIs & Performance
        "kpi": {
            "kpi_trends": "KPI प्रवृत्तियाँ",
            "kpi_subtitle": "दिशात्मक अंतर्दृष्टि के साथ प्रदर्शन संकेतक",
            "performance_up": "प्रदर्शन में सुधार",
            "performance_down": "प्रदर्शन में गिरावट",
            "stable": "स्थिर",
            "trend": "प्रवृत्ति",
            "direction": "दिशा",
        },
        
        # Forecasting
        "forecast": {
            "forecast_summary": "पूर्वानुमान सारांश",
            "forecast_ready": "पूर्वानुमान मॉडल विश्लेषण के लिए तैयार है।",
            "forecast_generated": "{count} पूर्वानुमान तैयार किए गए",
            "predictions": "पूर्वानुमान",
            "confidence": "आत्मविश्वास",
            "trend_up": "ऊपर की ओर प्रवृत्ति का पता चला",
            "trend_down": "नीचे की ओर प्रवृत्ति का पता चला",
            "trend_stable": "स्थिर प्रवृत्ति",
        },
        
        # Anomalies
        "anomaly": {
            "anomaly_detection": "विसंगति का पता लगाना",
            "anomaly_subtitle": "AI द्वारा हाइलाइट किए गए स्पाइक और ड्रॉप",
            "anomaly_found": "विसंगति का पता चला",
            "spike_detected": "स्पाइक का पता चला",
            "drop_detected": "ड्रॉप का पता चला",
        },
        
        # Business Intelligence
        "business": {
            "business_advisor": "व्यावसायिक सलाहकार",
            "business_advisor_tooltip": "मुफ्त AI-संचालित व्यावसायिक अंतर्दृष्टि, KPIs और सिफारिशें प्राप्त करें",
            "executive_summary": "कार्यकारी सारांश",
            "top_actions": "शीर्ष कार्रवाइयाँ",
            "opportunities": "अवसर",
            "recommendations": "सिफारिशें",
            "risks": "जोखिम",
            "actions_prioritized": "अधिकतम प्रभाव के लिए प्राथमिकता वाली कार्रवाइयाँ",
            "impact": "प्रभाव",
            "high": "उच्च",
            "medium": "माध्यम",
            "low": "निम्न",
        },
        
        # Modes
        "mode": {
            "mode": "मोड",
            "business_mode": "व्यावसायिक मोड",
            "data_mode": "डेटा मोड",
            "eli5_mode": "सरल विवरण",
            "mode_summary_business": "कार्य-तैयार सुझाव, प्रभाव मेट्रिक्स और कार्यकारी विवरण।",
            "mode_summary_data": "तकनीकी प्रोफाइलिंग, वितरण पैटर्न, सहसंबंध और गुणवत्ता संकेत।",
            "mode_summary_eli5": "तेजी से समझने और आसान निर्णयों के लिए सरल भाषा अंतर्दृष्टि।",
        },
        
        # Visualizations
        "viz": {
            "visualizations": "दृश्यांकन",
            "showing_charts": "{visible} का {total} दृश्यांकन दिखा रहे हैं",
            "all_charts": "सभी",
            "no_charts_filter": "इस फ़िल्टर के लिए कोई चार्ट नहीं मिला।",
            "filter_fallback": "सभी उपलब्ध दृश्यांकन प्रदर्शित किए जा रहे हैं।",
            "no_visualizations": "कोई दृश्यांकन उपलब्ध नहीं",
            "no_visualization_data": "अभी कोई दृश्यांकन डेटा नहीं",
            "chart": "चार्ट",
            "type": "प्रकार",
            "histogram": "हिस्टोग्राम",
            "bar": "बार",
            "line": "लाइन",
            "box": "बॉक्स",
            "scatter": "बिखराव",
            "pie": "पाई",
            "heatmap": "हीट मैप",
        },
        
        # Q&A
        "qa": {
            "ask_your_data": "अपने डेटा से पूछें",
            "ask_subtitle": "अपने डेटासेट के बारे में प्राकृतिक भाषा प्रश्न",
            "ask_hint": "'कौन सी उत्पाद सबसे कम प्रदर्शन कर रही है?' जैसे प्रश्न आजमाएं",
            "ask_placeholder": "यहां अपना प्रश्न टाइप करें...",
            "ask_button": "पूछें",
            "ai_response": "AI प्रतिक्रिया",
            "ask_after_upload": "डेटासेट अपलोड करने के बाद अपने डेटा से पूछें",
            "no_data_for_questions": "प्राकृतिक भाषा प्रश्नों को सक्षम करने के लिए एक डेटासेट अपलोड करें।",
            "question_failed": "आपके प्रश्न को संसाधित नहीं कर सके। कृपया फिर से कोशिश करें।",
        },
        
        # Plans & Billing
        "billing": {
            "plan": "योजना",
            "basic_plan": "बेसिक",
            "premium_plan": "प्रीमियम",
            "trial_plan": "मुफ्त ट्रायल",
            "premium_feature": "प्रीमियम विशेषता",
            "upgrade_to_premium": "प्रीमियम में अपग्रेड करें",
            "trial_ends_in": "ट्रायल {days} दिनों में समाप्त होगा",
            "premium_renews_in": "प्रीमियम {days} दिनों में नवीनीकृत होगा",
            "trial_started": "ट्रायल सफलतापूर्वक शुरू हुआ",
            "trial_expired": "ट्रायल की समय सीमा समाप्त हो गई",
            "upgrade_complete": "अपग्रेड सफल",
            "upgrade_failed": "अपग्रेड विफल। कृपया फिर से कोशिश करें।",
        },
        
        # System Messages
        "system": {
            "loading": "लोड हो रहा है...",
            "saving": "सहेज रहे हैं...",
            "success": "सफलता",
            "error": "त्रुटि",
            "warning": "चेतावनी",
            "info": "जानकारी",
            "please_try_again": "कृपया फिर से कोशिश करें।",
            "loading_profile": "प्रोफाइल लोड हो रहा है...",
            "logout": "लॉगआउट",
            "light_mode": "प्रकाश मोड",
            "dark_mode": "अंधेरा मोड",
            "language": "भाषा",
        },
        
        # Error Messages
        "errors": {
            "connection_error": "कनेक्शन त्रुटि। अपना इंटरनेट जांचें।",
            "server_error": "सर्वर त्रुटि। बाद में कोशिश करें।",
            "unauthorized": "अनुमति नहीं। कृपया फिर से लॉगिन करें।",
            "invalid_file": "अमान्य फाइल प्रारूप। कृपया CSV अपलोड करें।",
            "file_too_large": "फाइल बहुत बड़ी है। अधिकतम आकार 100MB है।",
            "no_data": "कोई डेटा उपलब्ध नहीं।",
            "something_went_wrong": "कुछ गलत हुआ। कृपया फिर से कोशिश करें।",
        },
    },
    
    "hinglish": {
        # Auth
        "auth": {
            "welcome_back": "Welcome Back",
            "login": "Login karo",
            "signup": "Sign Up karo",
            "email": "Email address",
            "password": "Password",
            "confirm_password": "Password confirm karo",
            "create_account": "Account banao",
            "forgot_password": "Password bhool gaye?",
            "invalid_credentials": "Credentials galat hai",
            "signup_success": "Trial shuru ho gaya. Signup complete. Ab login karo.",
            "password_mismatch": "Passwords match nahi kar rahe.",
            "already_have_account": "Pehle se account hai? Login karo",
            "reset_password": "Password reset karo",
            "reset_link_sent": "Password reset ka link aapke email par bhej diya gaya.",
            "password_reset_success": "Password reset successful. Ab login karo.",
        },
        
        # Dashboard
        "dashboard": {
            "welcome": "Welcome",
            "overview": "Dekho",
            "visualizations": "Charts",
            "ask": "Apne data se pooch",
            "history": "Pehle ka kaam",
            "profile": "Mera profile",
            "workspace_overview": "Aapka workspace",
            "signed_in_as": "Aap logged in ho",
            "uploads": "Uploads",
            "latest_kpis": "Latest insights",
            "quality_score": "Data quality score",
        },
        
        # Upload & Analysis
        "upload": {
            "upload_csv_title": "Shuru karne ke liye CSV upload karo",
            "file_prompt": "File ko drag karke drop karo ya browse karo.",
            "analyze_dataset": "Dataset analyze karo",
            "analyzing": "Analysis ho raha hai...",
            "upload_success": "Dataset successfully upload aur analyze ho gaya.",
            "upload_failed": "Dataset upload nahi ho paya. Dobara try karo.",
            "analyzing_dataset": "Aapka dataset analyze ho raha hai",
            "loading_summary": "Premium insights, KPIs aur smart recommendations tayyar ho rahe hain.",
        },
        
        # Data Quality
        "quality": {
            "data_health": "Data ki quality",
            "quality_score": "Quality score",
            "missing": "Khaali jagah",
            "duplicates": "Duplicate entries",
            "clean": "Saaf data",
            "data_health_text": "Visual quality score with missing, duplicate aur clean data breakdown.",
            "technical_snapshot": "Technical details",
            "technical_snapshot_text": "Gaharai se data quality aur distribution metrics.",
            "columns": "Columns",
            "rows": "Rows",
            "missing_values": "Khaali values",
            "duplicate_rows": "Duplicate rows",
            "clean_data": "Saaf data",
        },
        
        # Analysis Results
        "analysis": {
            "data_story": "Data ki story",
            "summary": "Summary",
            "insights": "Insights",
            "key_findings": "Main findings",
            "top_category": "Top category",
            "export_original_csv": "Original CSV export karo",
            "download_cleaned_data": "Saaf kiya hua data download karo",
            "auto_clean_data": "Data ko automatically saaf karo",
            "cleaning_data": "Data saaf ho raha hai...",
            "cleaned_dataset_applied": "Saaf kiya hua dataset apply ho gaya.",
            "clean_data_failed": "Data saaf karne mein problem aayi. Dobara try karo.",
        },
        
        # KPIs & Performance
        "kpi": {
            "kpi_trends": "KPI trends",
            "kpi_subtitle": "Performance indicators with directional insights",
            "performance_up": "Performance badh gaya",
            "performance_down": "Performance gir gaya",
            "stable": "Stable hai",
            "trend": "Trend",
            "direction": "Direction",
        },
        
        # Forecasting
        "forecast": {
            "forecast_summary": "Forecast summary",
            "forecast_ready": "Forecast model analysis ke liye ready hai.",
            "forecast_generated": "{count} forecasts tayyar kiye gaye",
            "predictions": "Predictions",
            "confidence": "Confidence level",
            "trend_up": "Upward trend dekha gaya",
            "trend_down": "Downward trend dekha gaya",
            "trend_stable": "Stable trend",
        },
        
        # Anomalies
        "anomaly": {
            "anomaly_detection": "Unusual patterns",
            "anomaly_subtitle": "AI ne jo strange spikes aur drops dekhe hain",
            "anomaly_found": "Unusual pattern dekha gaya",
            "spike_detected": "Spike aayi",
            "drop_detected": "Drop aayi",
        },
        
        # Business Intelligence
        "business": {
            "business_advisor": "Business Advisor",
            "business_advisor_tooltip": "Free AI-powered business insights, KPIs aur recommendations",
            "executive_summary": "Executive summary",
            "top_actions": "Karne ke liye best kaam",
            "opportunities": "Opportunities",
            "recommendations": "Recommendations",
            "risks": "Risks",
            "actions_prioritized": "Best kaam ko priority ke saath",
            "impact": "Impact",
            "high": "Bahut zyada",
            "medium": "Thoda",
            "low": "Kam",
        },
        
        # Modes
        "mode": {
            "mode": "mode",
            "business_mode": "Business mode",
            "data_mode": "Data mode",
            "eli5_mode": "Aasan bhasha mein",
            "mode_summary_business": "Action-ready suggestions, impact metrics aur executive narrative.",
            "mode_summary_data": "Technical profiling, distribution patterns, correlation aur quality signals.",
            "mode_summary_eli5": "Aasan bhasha mein insights taaki jaldi samajh aaye.",
        },
        
        # Visualizations
        "viz": {
            "visualizations": "Charts aur diagrams",
            "showing_charts": "{visible} of {total} visualizations dekh rahe hain",
            "all_charts": "Sab",
            "no_charts_filter": "Is filter mein koi chart nahi aayi.",
            "filter_fallback": "Sab available visualizations dekh rahe hain.",
            "no_visualizations": "Koi chart nahi hai",
            "no_visualization_data": "Abhi chart ka data nahi hai",
            "chart": "Chart",
            "type": "Type",
            "histogram": "Histogram",
            "bar": "Bar chart",
            "line": "Line chart",
            "box": "Box plot",
            "scatter": "Scatter plot",
            "pie": "Pie chart",
            "heatmap": "Heatmap",
        },
        
        # Q&A
        "qa": {
            "ask_your_data": "Apne data se pooch",
            "ask_subtitle": "Natural language mein apne dataset ke baare mein sawal poocho",
            "ask_hint": "'Konsa product sabse kaam perform kar raha hai?' jaisa pooch sakte ho",
            "ask_placeholder": "Yaha apna sawal likho...",
            "ask_button": "Pooch",
            "ai_response": "AI ka jawab",
            "ask_after_upload": "Dataset upload karne ke baad pooch sakte ho",
            "no_data_for_questions": "Natural language questions ke liye pehle dataset upload karo.",
            "question_failed": "Aapke sawal ko process nahi kar sake. Dobara try karo.",
        },
        
        # Plans & Billing
        "billing": {
            "plan": "plan",
            "basic_plan": "Basic",
            "premium_plan": "Premium",
            "trial_plan": "Free Trial",
            "premium_feature": "Premium feature",
            "upgrade_to_premium": "Premium mein upgrade karo",
            "trial_ends_in": "Trial {days} din mein khatm hoga",
            "premium_renews_in": "Premium {days} din mein renew hoga",
            "trial_started": "Trial successfully shuru ho gaya",
            "trial_expired": "Trial khatm ho gaya",
            "upgrade_complete": "Upgrade successful hua",
            "upgrade_failed": "Upgrade nahi ho paya. Dobara try karo.",
        },
        
        # System Messages
        "system": {
            "loading": "Load ho raha hai...",
            "saving": "Save ho raha hai...",
            "success": "Success",
            "error": "Error aayi",
            "warning": "Warning",
            "info": "Information",
            "please_try_again": "Kripya dobara try karo.",
            "loading_profile": "Profile load ho raha hai...",
            "logout": "Logout",
            "light_mode": "Light theme",
            "dark_mode": "Dark theme",
            "language": "Bhasha",
        },
        
        # Error Messages
        "errors": {
            "connection_error": "Internet se connection nahi ho raha.",
            "server_error": "Server mein problem hai. Baad mein dobara try karo.",
            "unauthorized": "Permission nahi hai. Dobara login karo.",
            "invalid_file": "File galat format mein hai. CSV upload karo.",
            "file_too_large": "File bahut badi hai. Maximum 100MB ho sakti hai.",
            "no_data": "Koi data nahi hai.",
            "something_went_wrong": "Kuch galat ho gaya. Dobara try karo.",
        },
    }
}


def get_translation(language: str, section: str, key: str, **kwargs) -> str:
    """
    Get translated string for a given language, section, and key.
    Supports parameter interpolation with **kwargs.
    
    Example:
        get_translation("hi", "forecast", "forecast_generated", count=5)
        # Returns: "5 पूर्वानुमान तैयार किए गए"
    """
    lang_dict = TRANSLATIONS.get(language) or TRANSLATIONS["en"]
    section_dict = lang_dict.get(section, {})
    text = section_dict.get(key, key)
    
    # Support simple string formatting
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    
    return text


def get_nested_translation(language: str, path: str, **kwargs) -> str:
    """
    Get translation using dot notation path.
    
    Example:
        get_nested_translation("hi", "forecast.forecast_generated", count=5)
    """
    parts = path.split(".")
    section = parts[0] if len(parts) > 0 else ""
    key = parts[1] if len(parts) > 1 else ""
    return get_translation(language, section, key, **kwargs)
