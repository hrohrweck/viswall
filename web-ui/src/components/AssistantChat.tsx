import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Shield, Check, Lightbulb, Wand2, Play } from 'lucide-react'

interface TestCase {
  name: string
  should: string
}

interface RuleData {
  rule: {
    name: string
    chain: string
    action: string
    protocol?: string
    src_ip?: string
    dst_ip?: string
    src_port?: number
    dst_port?: number
    interface_in?: string
    interface_out?: string
    log?: boolean
  }
  explanation: string
  security_notes: string
  suggested_tests: TestCase[]
}

interface TestSuggestionData {
  test_cases: {
    name: string
    description: string
    packet: {
      src_ip: string
      dst_ip: string
      protocol: string
      src_port?: number
      dst_port: number
    }
    expected_action: string
    critical: boolean
  }[]
  coverage: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'rule_suggestion' | 'test_suggestion' | 'explanation'
  data?: RuleData | TestSuggestionData
  timestamp: Date
}

export function AssistantChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm your Viswall configuration assistant. I can help you:\n\n• Create firewall rules\n• Generate test cases\n• Set up VPN or mail\n• Explain configurations\n• Troubleshoot issues\n\nWhat would you like to do?",
      type: 'text',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const suggestions = [
    { icon: Shield, text: "Block SSH from the internet", category: "Firewall" },
    { icon: Play, text: "Test web server access", category: "Testing" },
    { icon: Wand2, text: "Set up VPN for remote workers", category: "VPN" },
    { icon: Lightbulb, text: "Why is port 22 blocked?", category: "Explain" },
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setShowSuggestions(false)

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))

    // Mock response based on input
    let assistantMessage: Message

    if (input.toLowerCase().includes('block ssh') || input.toLowerCase().includes('ssh')) {
      assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I've created a firewall rule to block SSH from the internet. Here's what it does:",
        type: 'rule_suggestion',
        data: {
          rule: {
            name: 'Block WAN SSH',
            chain: 'input',
            action: 'drop',
            protocol: 'tcp',
            dst_port: 22,
            interface_in: 'eth0',
            log: true
          },
          explanation: 'This rule drops all incoming SSH connections from the WAN interface (eth0). It logs attempts for monitoring.',
          security_notes: '✓ Good security practice - SSH should not be exposed to the internet. Consider using VPN for remote access.',
          suggested_tests: [
            { name: 'SSH blocked from WAN', should: 'drop' },
            { name: 'SSH works from LAN', should: 'accept' }
          ]
        },
        timestamp: new Date()
      }
    } else if (input.toLowerCase().includes('test')) {
      assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I've generated test cases to verify your firewall configuration:",
        type: 'test_suggestion',
        data: {
          test_cases: [
            {
              name: 'LAN to Internet HTTP',
              description: 'Verify HTTP traffic from LAN to internet works',
              packet: { src_ip: '192.168.1.100', dst_ip: '8.8.8.8', protocol: 'tcp', dst_port: 80 },
              expected_action: 'accept',
              critical: true
            },
            {
              name: 'Block WAN SSH',
              description: 'Verify SSH from internet is blocked',
              packet: { src_ip: '203.0.113.100', dst_ip: '192.0.2.1', protocol: 'tcp', dst_port: 22 },
              expected_action: 'drop',
              critical: true
            }
          ],
          coverage: 'Covers basic connectivity and security rules'
        },
        timestamp: new Date()
      }
    } else {
      assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I understand you want help with that. Could you provide more details? For example:\n\n• Specific IP addresses or networks\n• Port numbers\n• Which direction the traffic should flow\n• What action you want (allow/block)",
        type: 'text',
        timestamp: new Date()
      }
    }

    setMessages(prev => [...prev, assistantMessage])
    setIsLoading(false)
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const renderMessageContent = (message: Message) => {
    if (message.type === 'rule_suggestion' && message.data) {
      const data = message.data as RuleData
      return (
        <div className="space-y-4">
          <p>{message.content}</p>
          
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-900">Suggested Rule</h4>
              <span className={`px-2 py-1 text-xs rounded ${
                data.rule.action === 'accept' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {data.rule.action.toUpperCase()}
              </span>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex">
                <span className="w-24 text-gray-600">Name:</span>
                <span className="font-mono">{data.rule.name}</span>
              </div>
              <div className="flex">
                <span className="w-24 text-gray-600">Chain:</span>
                <span className="font-mono">{data.rule.chain}</span>
              </div>
              {data.rule.protocol && (
                <div className="flex">
                  <span className="w-24 text-gray-600">Protocol:</span>
                  <span className="font-mono">{data.rule.protocol}</span>
                </div>
              )}
              {data.rule.dst_port && (
                <div className="flex">
                  <span className="w-24 text-gray-600">Port:</span>
                  <span className="font-mono">{data.rule.dst_port}</span>
                </div>
              )}
              {data.rule.interface_in && (
                <div className="flex">
                  <span className="w-24 text-gray-600">Interface:</span>
                  <span className="font-mono">{data.rule.interface_in}</span>
                </div>
              )}
            </div>

            <div className="mt-4 p-3 bg-blue-50 rounded text-sm">
              <p className="text-blue-900"><strong>Explanation:</strong> {data.explanation}</p>
            </div>

            <div className="mt-3 p-3 bg-green-50 rounded text-sm">
              <p className="text-green-900">{data.security_notes}</p>
            </div>
          </div>

          {data.suggested_tests.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-3">Suggested Tests</h4>
              <div className="space-y-2">
                {data.suggested_tests.map((test: TestCase, idx: number) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-600" />
                    <span>{test.name} (should {test.should})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button className="flex-1 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">
              Add to Firewall
            </button>
            <button className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">
              Test in Simulator
            </button>
          </div>
        </div>
      )
    }

    if (message.type === 'test_suggestion' && message.data) {
      const data = message.data as TestSuggestionData
      return (
        <div className="space-y-4">
          <p>{message.content}</p>
          
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3">Generated Test Cases</h4>
            
            <div className="space-y-3">
              {data.test_cases.map((test: TestSuggestionData['test_cases'][number], idx: number) => (
                <div key={idx} className="p-3 bg-white rounded border border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{test.name}</span>
                    {test.critical && (
                      <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">Critical</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{test.description}</p>
                  <div className="mt-2 text-sm font-mono bg-gray-100 p-2 rounded">
                    {test.packet.protocol} {test.packet.src_ip}:{test.packet.src_port || 'any'} → {test.packet.dst_ip}:{test.packet.dst_port}
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-sm text-gray-600">Expected:</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      test.expected_action === 'accept' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {test.expected_action.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <p className="mt-3 text-sm text-gray-600">{data.coverage}</p>
          </div>

          <div className="flex gap-2">
            <button className="flex-1 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">
              Run Tests
            </button>
            <button className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">
              Add to Test Suite
            </button>
          </div>
        </div>
      )
    }

    return <p className="whitespace-pre-line">{message.content}</p>
  }

  return (
    <div className="h-full flex flex-col bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">Configuration Assistant</h2>
            <p className="text-sm text-gray-600">Powered by AI</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              message.role === 'user' ? 'bg-gray-200' : 'bg-primary-100'
            }`}>
              {message.role === 'user' ? (
                <User className="w-5 h-5 text-gray-600" />
              ) : (
                <Bot className="w-5 h-5 text-primary-600" />
              )}
            </div>
            
            <div className={`max-w-[80%] rounded-lg p-3 ${
              message.role === 'user' 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-100 text-gray-900'
            }`}>
              {renderMessageContent(message)}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {showSuggestions && (
        <div className="px-4 pb-2">
          <p className="text-sm text-gray-500 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion.text)}
                className="flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition-colors"
              >
                <suggestion.icon className="w-4 h-4" />
                {suggestion.text}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything about your configuration..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
