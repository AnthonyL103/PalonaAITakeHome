import { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, Send, RotateCcw, ShoppingBag, Sparkles} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useWebSocket } from './WebSocket';

interface Message {
  type: 'user' | 'agent' | 'error' | 'tool';
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
  const [isResetting, setIsResetting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);


const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploadingImage(true);
    
    try {
      console.log("Uploading image:", file);
      const preview = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
      
      setSelectedImage64(preview);
      
      const formData = new FormData();
      formData.append('image', file);
      
      const response = await fetch('http://localhost:8000/upload_image', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Upload failed');
      
      const data = await response.json();
      setSelectedImage(data.image_path);
      
      console.log("Image uploaded, server path:", data.image_path);
      
    } catch (error) {
      console.error('Image upload error:', error);
      setSelectedImage64(null);
      setSelectedImage(null);
    } finally {
      setIsUploadingImage(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
};
  
  const handleWebSocketMessage = useCallback((message: any) => {
    console.log('Received WebSocket message:', message);
    
    if (message.type === 'tool') {
      const toolMessage: Message = {
        type: 'tool',
        content: message.content,
        timestamp: new Date()
      };
      
      setConversation((prev: Message[]) => [...prev, toolMessage]);
    } else if (message.type === 'error') {
      const errorMessage: Message = { 
        type: 'error', 
        content: message.message, 
        timestamp: new Date() 
      };
      setConversation((prev: Message[]) => [...prev, errorMessage]);
    }
    
  }, []);
  
  const { isConnected } = useWebSocket(handleWebSocketMessage);
  
  console.log("Is webhook connected?", isConnected)

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
    setSelectedImage64(null);

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
      setIsResetting(true);
      await fetch('http://localhost:8000/reset_conversation', {
        method: 'POST',
      });
      setConversation([]);
      setPrompt('');
      setSelectedImage(null);
      setSelectedImage64(null);
    } catch (err) {
      console.error('Reset error:', err);
    } finally {
      setIsResetting(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const exampleQuestions = [
    "Show me Apple headphones under $200",
    "Find laptops between $500 and $1000",
    "Highly rated smartphones in stock",
    "Affordable sports equipment"
  ];

  return (
    <div className="min-h-screen bg-amber-50" style={{
      backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(251, 191, 36, 0.03) 2px, rgba(251, 191, 36, 0.03) 4px)',
    }}>
      <div className="max-w-5xl mx-auto p-4 h-screen flex flex-col">
        
        <div className="bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-t-lg shadow-lg border-4 border-orange-800">
          <div className="p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white rounded-full p-3 border-4 border-orange-800">
                <ShoppingBag className="w-8 h-8 text-orange-600" />
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight" style={{ fontFamily: 'Impact, sans-serif' }}>
                  CARTPAL SHOPPING ASSISTANT
                </h1>
                <p className="text-orange-100 font-semibold">Your AI-Powered Product Expert • EST. 2025</p>
              </div>
            </div>
            <button
              onClick={resetConversation}
              disabled={isLoading}
              className="bg-orange-800 hover:bg-orange-900 px-4 py-2 rounded font-bold border-2 border-orange-950 transition-all hover:translate-y-0.5 disabled:opacity-50"
              title="Reset conversation"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>
          
        
        </div>

        <div className="flex-1 overflow-y-auto bg-white border-l-4 border-r-4 border-orange-800 p-6 space-y-4" style={{
          backgroundImage: 'linear-gradient(0deg, rgba(251, 191, 36, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(251, 191, 36, 0.02) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}>
          {conversation.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
              <div className="bg-orange-600 rounded-full p-6 border-4 border-orange-800" >
                <Sparkles className="w-16 h-16 text-white" />
              </div>
              
              <div className="bg-yellow-100 border-4 border-orange-800 rounded-lg p-8 max-w-2xl" >
                <h2 className="text-3xl font-black text-orange-900 mb-4" style={{ fontFamily: 'Impact, sans-serif' }}>
                  WELCOME TO THE FUTURE OF SHOPPING!
                </h2>
                <p className="text-lg text-gray-700 font-semibold mb-6">
                  I'm CartPal, your intelligent shopping companion. Here's what I can do:
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                  <div className="bg-white p-4 rounded border-2 border-orange-800">
                    <div className="font-black text-orange-600 mb-2 text-lg">SMART SEARCH</div>
                    <div className="text-sm text-gray-600">Find products with natural language</div>
                  </div>
                  <div className="bg-white p-4 rounded border-2 border-orange-800">
                    <div className="font-black text-orange-600 mb-2 text-lg">PRICE FILTERS</div>
                    <div className="text-sm text-gray-600">Set your budget, get exact matches</div>
                  </div>
                  <div className="bg-white p-4 rounded border-2 border-orange-800">
                    <div className="font-black text-orange-600 mb-2 text-lg">IMAGE SEARCH</div>
                    <div className="text-sm text-gray-600">Upload photos, find similar items</div>
                  </div>
                </div>
              </div>
              
              <div className="w-full max-w-2xl">
                <p className="text-sm font-bold text-orange-800 mb-3 uppercase tracking-wide">Try These Searches:</p>
                <div className="grid grid-cols-1 gap-2">
                  {exampleQuestions.map((question, idx) => (
                    <button
                      key={idx}
                      onClick={() => setPrompt(question)}
                      className="text-left p-4 bg-orange-100 hover:bg-orange-200 border-2 border-orange-800 rounded font-semibold text-gray-800 transition-all hover:translate-x-1"
                    >
                      ▸ {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {conversation.map((message, index) => (
                <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-3xl rounded-lg p-4 border-4 ${
                    message.type === 'user' 
                      ? 'bg-orange-600 text-white border-orange-800' 
                      : message.type === 'error'
                      ? 'bg-red-100 text-red-800 border-red-600'
                      : 'bg-yellow-50 text-gray-900 border-orange-800'
                  }`} >
                    {message.image && (
                      <img 
                        src={message.image} 
                        alt="Uploaded" 
                        className="rounded border-2 border-orange-800 mb-3 max-w-xs"
                      />
                    )}
                    
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown
                        components={{
                          h1: (props) => <h1 className="text-2xl font-black mb-3 text-orange-900" style={{ fontFamily: 'Impact, sans-serif' }} {...props} />,
                          h2: (props) => <h2 className="text-xl font-black mb-2 text-orange-800" style={{ fontFamily: 'Impact, sans-serif' }} {...props} />,
                          h3: (props) => <h3 className="text-lg font-bold mb-2 text-orange-700" {...props} />,
                          p: (props) => <p className="mb-3 leading-relaxed" {...props} />,
                          ul: (props) => <ul className="list-none space-y-2 mb-3" {...props} />,
                          ol: (props) => <ol className="list-decimal ml-5 space-y-2 mb-3" {...props} />,
                          li: (props) => <li className="flex items-start gap-2" {...props}><span className="text-orange-600 font-bold">▸</span><span className="flex-1">{props.children}</span></li>,
                          strong: (props) => <strong className="font-black text-orange-900" {...props} />,
                          em: (props) => <em className="italic text-gray-700" {...props} />,
                          hr: () => <hr className="my-4 border-2 border-orange-300" />,
                          blockquote: (props) => (
                            <blockquote className="border-l-4 border-orange-600 pl-4 italic my-3 bg-orange-50 py-2" {...props} />
                          ),
                        }}
                      >
                       
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    
                    {message.imageUrls && message.imageUrls.length > 0 && (
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3">
                        {message.imageUrls.map((imageUrl, idx) => (
                          <div key={idx} className="bg-white rounded overflow-hidden border-4 border-orange-800 hover:scale-105 transition-transform" >
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
                    
                    <div className={`text-xs mt-3 font-semibold ${message.type === 'user' ? 'text-orange-100' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-yellow-50 border-4 border-orange-800 rounded-lg p-4" >
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-orange-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-3 h-3 bg-orange-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-3 h-3 bg-orange-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="bg-orange-600 border-4 border-orange-800 rounded-b-lg p-4" >
          {selectedImage64 && (
            <div className="mb-3 relative inline-block">
                <img 
                src={selectedImage64} 
                alt="Preview" 
                className={`h-20 rounded border-4 border-orange-800 ${isUploadingImage ? 'opacity-50' : ''}`}
                />
                {isUploadingImage && (
                <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded">
                    <div className="w-3 h-3 bg-white rounded-full animate-bounce"></div>
                </div>
                )}
                <button
                onClick={() => {
                    setSelectedImage64(null);
                    setSelectedImage(null);
                }}
                disabled={isUploadingImage}
                className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-7 h-7 flex items-center justify-center hover:bg-red-700 font-bold border-2 border-red-800 disabled:opacity-50"
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
              className="p-3 bg-orange-800 hover:bg-orange-900 rounded border-2 border-orange-950 transition-all hover:translate-y-0.5 disabled:opacity-50"
              title="Upload image"
            >
              <Camera className="w-5 h-5 text-white" />
            </button>
            
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask about products, set your budget, or upload an image..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border-4 border-orange-800 rounded font-semibold focus:outline-none focus:ring-4 focus:ring-orange-400 disabled:opacity-50"
            />
            
            <button
            onClick={() => handleSubmit()}
            disabled={isLoading || isUploadingImage || (!prompt.trim() && !selectedImage)}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded font-black border-2 border-green-800 transition-all hover:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            style={{ fontFamily: 'Impact, sans-serif' }}
            >
            <Send className="w-5 h-5" />
            {isUploadingImage ? 'UPLOADING...' : isLoading ? 'SENDING...' : isResetting ? 'RESETTING...' : 'SEND'}
            </button>
          </div>
          
        </div>
      </div>
    </div>
  );
}