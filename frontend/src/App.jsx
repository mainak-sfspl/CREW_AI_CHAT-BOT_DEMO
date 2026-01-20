import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Sparkles, Loader2, Download } from 'lucide-react';

function App() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    { 
      type: 'bot', 
      text: 'Hello! I am the Sampurna IT Support Assistant. I can help with policies, assets, and technical issues.' 
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // --- NEW: Download Chat History ---
  const handleDownload = () => {
    const chatText = messages.map(m => `${m.type.toUpperCase()}: ${m.text}`).join('\n\n');
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sampurna_chat_${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMsg = { type: 'user', text: question };

    // 1. Prepare History (Last 5 exchanges to keep context)
    // We act like a "sliding window" of memory
    const recentHistory = messages.slice(-5).map(m => `${m.type === 'user' ? 'User' : 'Bot'}: ${m.text}`);

    setMessages(prev => [...prev, userMsg]);
    setQuestion('');
    setIsLoading(true);

    try {
      // 2. Send Question + History to Backend
      // CHANGE IP HERE IF NEEDED
      const response = await axios.post('http://172.16.1.53:8000/ask', {
        question: userMsg.text,
        chat_history: recentHistory 
      });

      setMessages(prev => [...prev, { type: 'bot', text: response.data.answer }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { type: 'bot', text: "Error: Server unreachable. Please check connection." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-gray-100 font-sans">

      {/* Header with Download Button */}
      <header className="flex items-center justify-between p-4 border-b border-gray-800 bg-slate-900/90 sticky top-0 z-10">
        <div className="flex items-center">
            <img src="/logo.png" alt="Logo" className="w-10 h-10 rounded-full bg-white/10 p-1" />
            <div className="ml-3">
                <h1 className="text-lg font-bold text-blue-400 flex items-center gap-2">
                  Sampurna IT <Sparkles size={14} className="text-yellow-400" />
                </h1>
                <p className="text-[10px] text-gray-400">Context Aware • Multilingual</p>
            </div>
        </div>

        <button 
            onClick={handleDownload}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors text-gray-300 flex items-center gap-2 text-xs font-medium border border-slate-700"
            title="Download Chat History"
        >
            <Download size={16} />
            <span className="hidden sm:inline">Save Chat</span>
        </button>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start max-w-[85%] ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center mt-1 shrink-0 ${
                  msg.type === 'user' ? 'ml-3 bg-blue-600' : 'mr-3 bg-emerald-600'
                }`}>
                  {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className={`p-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.type === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none' 
                    : 'bg-slate-800 border border-slate-700 text-gray-200 rounded-tl-none'
                }`}>
                  {msg.text}
                </div>
              </div>
            </motion.div>
          ))}

          {isLoading && (
            <div className="flex items-center ml-12 text-gray-400 text-sm">
              <Loader2 className="animate-spin mr-2" size={16} /> 
              <span className="animate-pulse">Thinking...</span>
            </div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-800/50 border-t border-slate-700">
        <form onSubmit={handleAsk} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask me anything..."
            className="w-full bg-slate-900 text-white rounded-full py-3.5 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-slate-700 shadow-lg"
          />
          <button 
            type="submit" 
            disabled={isLoading || !question.trim()}
            className="absolute right-2 p-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-full text-white transition-all"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
