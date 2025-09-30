import { useState, useRef, useEffect } from 'react';
import { Camera, Send, RotateCcw, ShoppingBag, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  type: 'user' | 'agent' | 'error';
  content: string;
  timestamp: Date;
  image?: string;
  imageUrls?: string[];
}

export default function CommerceAgent() {
  const [prompt, setPrompt] = useState('');
  const [conversation, setConversation] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedImage64, setSelectedImage64] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (file) {
    const reader = new FileReader();
    reader.onloadend = () => {
      setSelectedImage64(reader.result as string); 
    };
    reader.readAsDataURL(file);
    
    const formData = new FormData();
    formData.append('image', file);
    
    const response = await fetch('http://localhost:8000/upload_image', {
      method: 'POST',
      body: formData,
    });
    
    const data = await response.json();
    setSelectedImage(data.image_path); 
  }
};

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (!prompt.trim() && !selectedImage) return;

    setIsLoading(true);

    const userMessage: Message = {
    type: 'user',
    content: prompt || 'Search by image',
    timestamp: new Date(),
    image: selectedImage64 || undefined,  
    };

    setConversation(prev => [...prev, userMessage]);

    const currentPrompt = prompt;
    setPrompt('');
    setSelectedImage(null);

    try {
      const response = await fetch('http://localhost:8000/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: currentPrompt, image: selectedImage }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      const data = await response.json();
      
      console.log('API response data:', data);

      let imageUrls: string[] = [];
      if (data.image_result) {
        try {
          imageUrls = JSON.parse(data.image_result);
        } catch (e) {
          console.error('Failed to parse image URLs:', e);
        }
      }

      const agentMessage: Message = {
        type: 'agent',
        content: data.text_result || 'No response',
        timestamp: new Date(),
        imageUrls: imageUrls.length > 0 ? imageUrls : undefined,
      };

      setConversation(prev => [...prev, agentMessage]);
    } catch (err) {
      const errorMessage: Message = {
        type: 'error',
        content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = async () => {
    try {
      setIsLoading(true);
      await fetch('http://localhost:8000/reset_conversation', {
        method: 'POST',
      });
      setConversation([]);
      setPrompt('');
      setSelectedImage(null);
    } catch (err) {
      console.error('Reset error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const exampleQuestions = [
    "What's your name?",
    "Recommend me a t-shirt for sports",
    "Show me winter jackets under $100",
    "What can you help me with?"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{ height: '90vh' }}>
        
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center gap-3">
            <ShoppingBag className="w-8 h-8" />
            <div>
              <h1 className="text-2xl font-bold">Commerce AI Assistant</h1>
              <p className="text-blue-100 text-sm">Ask questions, get recommendations, search by image</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {conversation.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
              <Sparkles className="w-16 h-16 text-indigo-400" />
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome! 👋</h2>
                <p className="text-gray-600 mb-6">I'm your AI shopping assistant. I can help you:</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="font-semibold text-blue-700 mb-1">💬 Chat</div>
                    <div className="text-sm text-gray-600">Ask me anything!</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="font-semibold text-green-700 mb-1">🛍️ Recommend</div>
                    <div className="text-sm text-gray-600">Get product suggestions</div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="font-semibold text-purple-700 mb-1">📸 Image Search</div>
                    <div className="text-sm text-gray-600">Upload photos to find similar items</div>
                  </div>
                </div>
              </div>
              
              <div className="w-full max-w-xl">
                <p className="text-sm text-gray-500 mb-3">Try asking:</p>
                <div className="grid grid-cols-1 gap-2">
                  {exampleQuestions.map((question, idx) => (
                    <button
                      key={idx}
                      onClick={() => setPrompt(question)}
                      className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition-colors"
                    >
                      "{question}"
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {conversation.map((message, index) => (
                <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-3xl rounded-2xl p-4 ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {message.image && (
                      <img 
                        src={message.image} 
                        alt="Uploaded" 
                        className="rounded-lg mb-2 max-w-xs"
                      />
                    )}
                    
                    <div className={`prose prose-sm max-w-none ${
                      message.type === 'user' ? 'prose-invert' : ''
                    }`}>
                      <ReactMarkdown
                        components={{
                          h1: (props) => <h1 className="text-xl font-bold mb-2" {...props} />,
                          h2: (props) => <h2 className="text-lg font-bold mb-2" {...props} />,
                          h3: (props) => <h3 className="text-base font-semibold mb-1" {...props} />,
                          p: (props) => <p className="mb-2" {...props} />,
                          ul: (props) => <ul className="list-disc ml-4 mb-2" {...props} />,
                          ol: (props) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                          li: (props) => <li className="mb-1" {...props} />,
                          strong: (props) => <strong className="font-semibold" {...props} />,
                          em: (props) => <em className="italic" {...props} />,
                          code: (props) => (
                            <code className="bg-gray-200 px-1 py-0.5 rounded text-sm" {...props} />
                          ),
                          pre: (props) => (
                            <pre className="bg-gray-200 p-2 rounded overflow-x-auto" {...props} />
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    
                    {message.imageUrls && message.imageUrls.length > 0 && (
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3">
                        {message.imageUrls.map((imageUrl, idx) => (
                          <div key={idx} className="bg-white rounded-lg overflow-hidden shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                            <img 
                              src={imageUrl} 
                              alt={`Product ${idx + 1}`}
                              className="w-full h-40 object-cover"
                              onError={(e) => {
                                e.currentTarget.src = 'https://via.placeholder.com/150?text=Image+Not+Found';
                              }}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                    
                    <div className={`text-xs mt-2 ${message.type === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-2xl p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="border-t border-gray-200 bg-gray-50 p-4">
          {selectedImage64 && (  
            <div className="mb-3 relative inline-block">
                <img src={selectedImage64} alt="Preview" className="h-20 rounded-lg" />
                <button
                onClick={() => {
                    setSelectedImage64(null);
                    setSelectedImage(null);  
                }}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
                >
                ×
                </button>
            </div>
            )}
          
          <div className="flex gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              accept="image/*"
              className="hidden"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="p-3 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors disabled:opacity-50"
              title="Upload image"
            >
              <Camera className="w-5 h-5 text-gray-700" />
            </button>
            
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask about products, get recommendations..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            
            <button
              onClick={() => handleSubmit()}
              disabled={isLoading || (!prompt.trim() && !selectedImage)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              {isLoading ? 'Sending...' : 'Send'}
            </button>
            
            <button
              onClick={resetConversation}
              disabled={isLoading}
              className="p-3 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors disabled:opacity-50"
              title="Reset conversation"
            >
              <RotateCcw className="w-5 h-5 text-gray-700" />
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            💡 The assistant remembers your conversation context
          </p>
        </div>
      </div>
    </div>
  );
}