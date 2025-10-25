# 🎙️ Travel Voice Widget with Vapi

A modern, interactive voice AI widget for travel booking powered by Vapi AI.

## 🚀 Quick Start

### 1. Start Widget Server
```bash
cd widget
python -m http.server 4000
```

### 2. Open in Browser
```
http://localhost:4000
```

### 3. Configure Vapi Dashboard

**Your Assistant ID:** `dd90cfd5-f26c-4f1b-aa46-39aff3cb032e`

#### Required Steps:
1. Go to https://dashboard.vapi.ai
2. Find "VoiceAssistant (Copy)"
3. Click **PUBLISH** (if not already published)
4. Go to **Tools** section
5. Configure tool server URL: `http://localhost:8080/api/functions`

---

## 📁 Project Structure

```
vapi-voicebot/
├── widget/              # Frontend voice widget
│   ├── index.html      # Main HTML file
│   ├── favicon.svg     # Site icon
│   └── src/
│       ├── widget.js   # Widget logic
│       └── styles/
│           └── widget.css
├── backend/            # Backend API (if needed)
│   └── server.py
├── requirements.txt    # Python dependencies
└── package.json        # Node dependencies
```

---

## ⚙️ Configuration

### Widget Configuration
File: `widget/index.html` (line 78-83)

```javascript
window.myTripWidget = new TravelVoiceWidget({
    vapiPublicKey: '00ed1b9b-a752-4079-bc72-32986d840d52',
    vapiAssistantId: 'dd90cfd5-f26c-4f1b-aa46-39aff3cb032e',
    apiUrl: 'http://localhost:8080',
    position: 'bottom-right'
});
```

### Vapi Assistant Configuration

**Model:** GPT-4o  
**Voice:** Elliot (Vapi)  
**Transcriber:** Deepgram Nova-2  
**Language:** English

---

## 🔧 Troubleshooting

### Issue: 400 Bad Request Error

**Causes:**
1. Assistant not published
2. Wrong assistant ID
3. Invalid API key

**Solution:**
1. Verify assistant ID matches in widget
2. Publish assistant in Vapi dashboard
3. Check API key is correct

### Issue: AI Voice Not Speaking

**Causes:**
1. Microphone permission not granted
2. Assistant not published
3. Tool server URL not configured

**Solution:**
1. Grant microphone permission when prompted
2. Publish assistant in dashboard
3. Configure tool server URL in Tools section

### Issue: Widget Button Not Appearing

**Causes:**
1. Vapi SDK not loading
2. JavaScript errors
3. CSS not loading

**Solution:**
1. Check browser console (F12) for errors
2. Hard refresh: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)
3. Verify all files are being served correctly

---

## 🧪 Testing

### 1. Open Browser Console
- Press `F12`
- Go to Console tab

### 2. Click 🎙️ Button
- Look for initialization logs
- Grant microphone permission

### 3. Say "Hello"
- AI should respond with greeting
- Transcript should appear in chat

### 4. Check for Errors
- ✅ No 400 errors
- ✅ No SDK loading errors
- ✅ Call established successfully

---

## 📋 Essential Files Only

**Removed unnecessary files:**
- ❌ All documentation `.md` files (except this README)
- ❌ Configuration scripts
- ❌ Project tree files
- ❌ Upgrade summaries

**Kept essential files:**
- ✅ Widget source code
- ✅ Backend server (if used)
- ✅ Dependencies (requirements.txt, package.json)
- ✅ Configuration files (.env, .gitignore)
- ✅ This README

---

## 🔗 Important Links

- **Vapi Dashboard:** https://dashboard.vapi.ai
- **Widget URL:** http://localhost:4000
- **Backend URL:** http://localhost:8080 (if used)

---

## 📞 How It Works

1. **User clicks 🎙️** → Widget calls Vapi SDK
2. **Vapi SDK** → Establishes WebRTC connection
3. **Deepgram** → Transcribes user speech to text
4. **GPT-4o** → Processes conversation and generates response
5. **Vapi Voice** → Speaks response to user
6. **Widget** → Displays transcript in chat interface

---

## 🎯 Current Status

- ✅ Assistant ID updated and verified
- ✅ Widget server running on port 4000
- ✅ Vapi SDK loading correctly
- ⚠️ **Action Required:** Publish assistant in dashboard
- ⚠️ **Action Required:** Configure tool server URL

---

## 💡 Tips

- Always **hard refresh** after changes: `Cmd + Shift + R`
- Check **browser console** for detailed logs
- Use **F12 Developer Tools** to debug issues
- Test in **Chrome/Edge** for best compatibility
- Grant **microphone permission** when prompted

---

**Last Updated:** October 21, 2025  
**Status:** Ready for testing after dashboard configuration ✅

