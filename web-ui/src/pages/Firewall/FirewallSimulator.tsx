import { useState, useEffect, useRef } from 'react'
import { Play, Pause, RotateCcw, CheckCircle, XCircle, ChevronRight, Info } from 'lucide-react'

interface Packet {
  src_ip: string
  dst_ip: string
  protocol: string
  src_port?: number
  dst_port?: number
  interface_in: string
  interface_out: string
  flags: string[]
  connection_state: string
}

interface Rule {
  id: number
  name: string
  chain: string
  action: string
  src_ip?: string
  dst_ip?: string
  protocol?: string
  src_port?: number
  dst_port?: number
  interface_in?: string
  interface_out?: string
  state?: string
  log: boolean
  order: number
  enabled: boolean
}

interface SimulationStep {
  step: number
  type: 'entry' | 'chain_selection' | 'rule_evaluation' | 'action'
  description: string
  packet?: Packet
  chain?: string
  rule?: Rule
  matched?: boolean
  action?: string
  position: { x: number; y: number }
}

interface SimulationResult {
  packet: Packet
  steps: SimulationStep[]
  final_result: {
    final_action: string
    matched_rule?: { id: number; name: string }
    rules_evaluated: number
    processing_time_ms: number
  }
}

export function FirewallSimulator() {
  const [packet, setPacket] = useState<Packet>({
    src_ip: '192.168.1.100',
    dst_ip: '8.8.8.8',
    protocol: 'tcp',
    src_port: 54321,
    dst_port: 443,
    interface_in: 'eth1',
    interface_out: 'eth0',
    flags: ['SYN'],
    connection_state: 'NEW'
  })

  const [rules] = useState<Rule[]>([
    { id: 1, name: 'Block WAN SSH', chain: 'input', action: 'drop', dst_port: 22, interface_in: 'eth0', log: true, order: 10, enabled: true },
    { id: 2, name: 'Allow LAN to WAN', chain: 'forward', action: 'accept', interface_in: 'eth1', interface_out: 'eth0', log: false, order: 100, enabled: true },
    { id: 3, name: 'Block Bad IPs', chain: 'forward', action: 'drop', src_ip: '10.0.0.0/8', log: true, order: 50, enabled: true },
  ])

  useState({ eth0: 'wan', eth1: 'lan' })
  const [simulation, setSimulation] = useState<SimulationResult | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const runSimulation = async () => {
    // In real implementation, call API
    // For now, simulate the response
    const mockResult: SimulationResult = {
      packet,
      steps: [
        { step: 1, type: 'entry', description: `Packet enters via ${packet.interface_in}`, position: { x: 50, y: 200 } },
        { step: 2, type: 'chain_selection', description: "Packet routed to 'forward' chain", chain: 'forward', position: { x: 200, y: 200 } },
        { step: 3, type: 'rule_evaluation', description: 'Evaluating: Block Bad IPs', rule: rules[2], matched: false, position: { x: 350, y: 100 } },
        { step: 4, type: 'rule_evaluation', description: 'Evaluating: Block WAN SSH', rule: rules[0], matched: false, position: { x: 350, y: 200 } },
        { step: 5, type: 'rule_evaluation', description: 'Evaluating: Allow LAN to WAN', rule: rules[1], matched: true, position: { x: 350, y: 300 } },
        { step: 6, type: 'action', description: 'Final action: ACCEPT', action: 'accept', position: { x: 550, y: 200 } },
      ],
      final_result: {
        final_action: 'accept',
        matched_rule: { id: 2, name: 'Allow LAN to WAN' },
        rules_evaluated: 3,
        processing_time_ms: 0.05
      }
    }
    setSimulation(mockResult)
    setCurrentStep(0)
  }

  useEffect(() => {
    if (isPlaying && simulation) {
      const interval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev >= simulation.steps.length - 1) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [isPlaying, simulation])

  useEffect(() => {
    if (!canvasRef.current || !simulation) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const isDark = document.documentElement.classList.contains('dark')

    // Draw connections
    ctx.strokeStyle = isDark ? '#374151' : '#e5e7eb'
    ctx.lineWidth = 2
    ctx.beginPath()
    
    simulation.steps.forEach((step, index) => {
      if (index < simulation.steps.length - 1) {
        const next = simulation.steps[index + 1]
        ctx.moveTo(step.position.x + 40, step.position.y + 20)
        ctx.lineTo(next.position.x, next.position.y + 20)
      }
    })
    ctx.stroke()

    // Draw steps
    simulation.steps.forEach((step, index) => {
      const isActive = index <= currentStep
      const isCurrent = index === currentStep
      
      // Draw node
      ctx.beginPath()
      ctx.arc(step.position.x + 20, step.position.y + 20, 20, 0, Math.PI * 2)
      ctx.fillStyle = isActive ? (step.type === 'action' && step.action === 'accept' ? '#10b981' : step.type === 'action' && step.action === 'drop' ? '#ef4444' : '#3b82f6') : (isDark ? '#1f2937' : '#f3f4f6')
      ctx.fill()
      ctx.strokeStyle = isCurrent ? '#3b82f6' : (isDark ? '#4b5563' : '#d1d5db')
      ctx.lineWidth = isCurrent ? 3 : 1
      ctx.stroke()
      
      // Draw step number
      ctx.fillStyle = isActive ? 'white' : (isDark ? '#9ca3af' : '#6b7280')
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(String(step.step), step.position.x + 20, step.position.y + 25)
      
      // Draw label
      ctx.fillStyle = isDark ? '#d1d5db' : '#374151'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(step.type, step.position.x + 20, step.position.y + 55)
    })
  }, [simulation, currentStep])

  return (
    <div className="space-y-6">
      {/* Preview notice */}
      <div className="flex items-start gap-3 p-4 rounded-card border border-warning bg-warning-subtle" role="status">
        <Info className="h-5 w-5 text-warning shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-on-surface">Preview — not connected to a live instance</p>
          <p className="text-xs text-on-surface-muted mt-0.5">This simulator uses mock data for demonstration. Deploy an agent instance to enable live rule evaluation.</p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Firewall Rule Simulator</h2>
          <p className="text-gray-600 mt-1 dark:text-gray-400">Test firewall rules before deploying to production</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            disabled={!simulation}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-fg rounded-lg hover:bg-primary-hover disabled:opacity-50"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? 'Pause' : 'Play'}
          </button>
          
          <button
            onClick={() => { setCurrentStep(0); setIsPlaying(false); }}
            disabled={!simulation}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Packet Configuration */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 mb-4 dark:text-white">Test Packet</h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="sim-src-ip" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Source IP</label>
                <input
                  id="sim-src-ip"
                  type="text"
                  value={packet.src_ip}
                  onChange={(e) => setPacket({ ...packet, src_ip: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label htmlFor="sim-dst-ip" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Dest IP</label>
                <input
                  id="sim-dst-ip"
                  type="text"
                  value={packet.dst_ip}
                  onChange={(e) => setPacket({ ...packet, dst_ip: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="sim-protocol" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Protocol</label>
                <select
                  id="sim-protocol"
                  value={packet.protocol}
                  onChange={(e) => setPacket({ ...packet, protocol: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                >
                  <option value="tcp">TCP</option>
                  <option value="udp">UDP</option>
                  <option value="icmp">ICMP</option>
                </select>
              </div>
              <div>
                <label htmlFor="sim-src-port" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Src Port</label>
                <input
                  id="sim-src-port"
                  type="number"
                  value={packet.src_port}
                  onChange={(e) => setPacket({ ...packet, src_port: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label htmlFor="sim-dst-port" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Dst Port</label>
                <input
                  id="sim-dst-port"
                  type="number"
                  value={packet.dst_port}
                  onChange={(e) => setPacket({ ...packet, dst_port: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="sim-interface-in" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">In Interface</label>
                <select
                  id="sim-interface-in"
                  value={packet.interface_in}
                  onChange={(e) => setPacket({ ...packet, interface_in: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                >
                  <option value="eth0">eth0 (WAN)</option>
                  <option value="eth1">eth1 (LAN)</option>
                </select>
              </div>
              <div>
                <label htmlFor="sim-conn-state" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Conn State</label>
                <select
                  id="sim-conn-state"
                  value={packet.connection_state}
                  onChange={(e) => setPacket({ ...packet, connection_state: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                >
                  <option value="NEW">NEW</option>
                  <option value="ESTABLISHED">ESTABLISHED</option>
                  <option value="RELATED">RELATED</option>
                </select>
              </div>
            </div>

            <button
              onClick={runSimulation}
              className="w-full py-2 bg-primary text-primary-fg rounded-lg hover:bg-primary-hover"
            >
              Run Simulation
            </button>
          </div>
        </div>

        {/* Visualization */}
        <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 mb-4 dark:text-white">Packet Flow Visualization</h3>
          
          <div className="relative h-80 bg-gray-50 rounded-lg overflow-hidden dark:bg-gray-950">
            {simulation ? (
              <canvas
                ref={canvasRef}
                width={700}
                height={320}
                className="w-full h-full"
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                Configure packet and click "Run Simulation"
              </div>
            )}
          </div>

          {/* Step Details */}
          {simulation && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg dark:bg-blue-950/20">
              <div className="flex items-start gap-3">
                <ChevronRight className="w-5 h-5 text-blue-600 mt-0.5 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-800 dark:text-blue-300">{simulation.steps[currentStep].description}</p>
                </div>
              </div>
            </div>
          )}

          {simulation && (
            <div className="mt-4 p-4 border border-gray-200 rounded-lg dark:border-gray-700">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Simulation Result</h4>
              <div className="flex items-center gap-2">
                {simulation.final_result.final_action === 'accept' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-600" />
                )}
                <span className="text-sm font-medium capitalize dark:text-white">
                  {simulation.final_result.final_action}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
