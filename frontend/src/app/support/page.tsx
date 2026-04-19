"use client";

import { useState, useRef, useEffect } from "react";
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: Date;
}

const faqCategories = [
  {
    name: "Installatie",
    questions: [
      "Hoe installeer ik Shizuku?",
      "Hoe koppel ik een device?",
      "EmuFlow Agent installeren",
    ],
  },
  {
    name: "Controllers",
    questions: [
      "Welk profiel is het beste voor mij?",
      "Hoe pas ik een hotkey aan?",
      "Xbox controller koppelen",
    ],
  },
  {
    name: "BIOS",
    questions: [
      "Welke BIOS-bestanden heb ik nodig?",
      "Waar vind ik legale BIOS-bestanden?",
      "PS1 BIOS verificatie",
    ],
  },
  {
    name: "Hardware",
    questions: [
      "Welke handhelds worden ondersteund?",
      "Beste chipset voor emulatie?",
      "Odin 2 instellen",
    ],
  },
  {
    name: "Frontend",
    questions: [
      "ES-DE vs RetroArch",
      "Thema's instellen",
      "ROM-organisatie",
    ],
  },
  {
    name: "Updates",
    questions: [
      "Hoe werkt automatisch updaten?",
      "Obtainium configureren",
      "Rollback naar vorige versie",
    ],
  },
];

const initialMessages: Message[] = [
  {
    id: "welcome",
    role: "assistant",
    content:
      "Hallo! Ik ben de EmuFlow Support assistent. Ik help je met vragen over device-koppeling, emulatoren, controllers, BIOS-bestanden en meer. Stel gerust je vraag!",
    timestamp: new Date(),
  },
];

export default function SupportPage() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || sending) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);

    // Placeholder response — will connect to API
    setTimeout(() => {
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          "Bedankt voor je vraag! De AI Support API is nog in ontwikkeling. Binnenkort kan ik je hier volledig mee helpen. Bekijk ondertussen de FAQ categorieën aan de zijkant.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setSending(false);
    }, 800);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleFaqClick = (question: string) => {
    sendMessage(question);
  };

  const formatTime = (date: Date) =>
    date.toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          AI Support
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Stel vragen over EmuFlow, emulatoren, hardware en meer.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5 items-start">
        {/* Chat Window */}
        <div className="lg:col-span-3 bg-slate-800 rounded-xl border border-slate-700/50 flex flex-col h-[600px]">
          {/* Chat Header */}
          <div className="px-4 py-3 border-b border-slate-700/50 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm font-medium text-slate-300">
              EmuFlow Support
            </span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-violet-600 text-white rounded-br-sm"
                      : "bg-slate-700/70 text-slate-200 rounded-bl-sm"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <ChatBubbleLeftRightIcon className="w-3.5 h-3.5 text-violet-400" />
                      <span className="text-xs font-semibold text-violet-400">
                        EmuFlow Support
                      </span>
                    </div>
                  )}
                  <p>{msg.content}</p>
                  <p
                    className={`text-xs mt-1.5 ${
                      msg.role === "user" ? "text-violet-300" : "text-slate-500"
                    }`}
                  >
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-slate-700/70 rounded-xl rounded-bl-sm px-4 py-3">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className="p-3 border-t border-slate-700/50 flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Stel je vraag…"
              disabled={sending}
              className="flex-1 bg-slate-700/60 text-white text-sm placeholder-slate-500 rounded-lg px-4 py-2.5 border border-slate-600/50 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-colors disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="p-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors duration-150 flex-shrink-0"
              aria-label="Versturen"
            >
              <PaperAirplaneIcon className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* FAQ Sidebar */}
        <div className="space-y-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-1">
            Veelgestelde vragen
          </p>
          {faqCategories.map((cat) => (
            <div
              key={cat.name}
              className="bg-slate-800 rounded-xl border border-slate-700/50 overflow-hidden"
            >
              <div className="px-3 py-2 border-b border-slate-700/40">
                <p className="text-xs font-semibold text-violet-400">
                  {cat.name}
                </p>
              </div>
              <div className="p-1">
                {cat.questions.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => handleFaqClick(q)}
                    className="w-full text-left px-3 py-2 text-xs text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors duration-100"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
