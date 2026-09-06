import { useState } from 'react'
import { Play, CheckCircle, XCircle, AlertTriangle, FileJson, Info } from 'lucide-react'

interface TestCase {
  id: string
  name: string
  description: string
  packet: {
    src_ip: string
    dst_ip: string
    protocol: string
    dst_port: number
    interface_in: string
    connection_state: string
  }
  expected_action: string
  critical: boolean
  tags: string[]
}

interface TestResult {
  test_case: TestCase
  passed: boolean
  actual_action: string
  error_message?: string
  execution_time_ms: number
}

interface TestSuiteResult {
  total: number
  passed: number
  failed: number
  pass_rate: number
  critical_failures: string[]
  can_deploy: boolean
  results: TestResult[]
}

export function FirewallTestSuite() {
  const [testSuites] = useState([
    { id: 'basic', name: 'Basic Connectivity', description: 'Essential connectivity tests', count: 5 },
    { id: 'security', name: 'Security', description: 'Security-focused tests', count: 3 },
    { id: 'application', name: 'Applications', description: 'Application-specific tests', count: 3 },
  ])

  const [selectedSuites, setSelectedSuites] = useState<string[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<TestSuiteResult | null>(null)
  const [activeTab, setActiveTab] = useState<'suites' | 'results' | 'custom'>('suites')

  const runTests = async () => {
    setIsRunning(true)
    setActiveTab('results')

    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 2000))

    const mockResult: TestSuiteResult = {
      total: 11,
      passed: 9,
      failed: 2,
      pass_rate: 81.8,
      critical_failures: ['block-spoofed-internal'],
      can_deploy: false,
      results: [
        {
          test_case: {
            id: 'basic-internet-http',
            name: 'LAN to Internet HTTP',
            description: 'Verify HTTP traffic from LAN to internet works',
            packet: { src_ip: '192.168.1.100', dst_ip: '8.8.8.8', protocol: 'tcp', dst_port: 80, interface_in: 'eth1', connection_state: 'NEW' },
            expected_action: 'accept',
            critical: true,
            tags: ['basic', 'http']
          },
          passed: true,
          actual_action: 'accept',
          execution_time_ms: 0.5
        },
        {
          test_case: {
            id: 'block-wan-ssh',
            name: 'Block WAN SSH',
            description: 'Verify SSH from internet is blocked',
            packet: { src_ip: '203.0.113.100', dst_ip: '192.0.2.1', protocol: 'tcp', dst_port: 22, interface_in: 'eth0', connection_state: 'NEW' },
            expected_action: 'drop',
            critical: true,
            tags: ['security', 'ssh']
          },
          passed: true,
          actual_action: 'drop',
          execution_time_ms: 0.3
        },
        {
          test_case: {
            id: 'block-spoofed-internal',
            name: 'Block Spoofed Internal Traffic',
            description: 'Block traffic claiming to be from internal network but coming from WAN',
            packet: { src_ip: '192.168.1.50', dst_ip: '192.168.1.100', protocol: 'tcp', dst_port: 22, interface_in: 'eth0', connection_state: 'NEW' },
            expected_action: 'drop',
            critical: true,
            tags: ['security', 'spoofing']
          },
          passed: false,
          actual_action: 'accept',
          error_message: 'Expected drop, got accept - Spoofed traffic is being allowed!',
          execution_time_ms: 0.4
        },
      ]
    }

    setResult(mockResult)
    setIsRunning(false)
  }

  const toggleSuite = (suiteId: string) => {
    setSelectedSuites(prev => 
      prev.includes(suiteId) 
        ? prev.filter(id => id !== suiteId)
        : [...prev, suiteId]
    )
  }

  return (
    <div className="space-y-6">
      {/* Preview notice */}
      <div className="flex items-start gap-3 p-4 rounded-card border border-warning bg-warning-subtle" role="status">
        <Info className="h-5 w-5 text-warning shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-on-surface">Preview — not connected to a live instance</p>
          <p className="text-xs text-on-surface-muted mt-0.5">This test suite uses mock data for demonstration. Deploy an agent instance to run tests against live firewall rules.</p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Firewall Test Suite</h2>
          <p className="text-gray-600 mt-1 dark:text-gray-400">Validate firewall configurations with automated tests before deployment</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('custom')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <FileJson className="w-4 h-4 inline mr-2" />
            Custom Tests
          </button>

          <button
            onClick={runTests}
            disabled={selectedSuites.length === 0 || isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-fg rounded-lg hover:bg-primary-hover disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {isRunning ? 'Running...' : 'Run Tests'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
        {(['suites', 'results', 'custom'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 px-2 font-medium capitalize ${
              activeTab === tab 
                ? 'text-primary border-b-2 border-primary'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-white'
            }`}
          >
            {tab === 'suites' && `Test Suites (${selectedSuites.length} selected)`}
            {tab === 'results' && `Results ${result ? `(${result.passed}/${result.total})` : ''}`}
            {tab === 'custom' && 'Custom Tests'}
          </button>
        ))}
      </div>

      {/* Test Suites Tab */}
      {activeTab === 'suites' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {testSuites.map((suite) => (
            <div
              key={suite.id}
              role="button"
              tabIndex={0}
              aria-pressed={selectedSuites.includes(suite.id)}
              onClick={() => toggleSuite(suite.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  toggleSuite(suite.id)
                }
              }}
              className={`p-6 rounded-lg border-2 cursor-pointer transition-all ${
                selectedSuites.includes(suite.id)
                  ? 'border-primary bg-primary-subtle'
                  : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">{suite.name}</h3>
                  <p className="text-sm text-gray-600 mt-1 dark:text-gray-400">{suite.description}</p>
                  <span className="inline-block mt-3 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded dark:bg-gray-800 dark:text-gray-300">
                    {suite.count} tests
                  </span>
                </div>
                
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                  selectedSuites.includes(suite.id)
                    ? 'bg-primary border-primary'
                  : 'border-gray-300 dark:border-gray-600'
              }`}>
                  {selectedSuites.includes(suite.id) && <CheckCircle className="w-4 h-4 text-primary-fg" />}
                </div>
              </div>
            </div>
          ))}

          {/* Custom Test Card */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => setActiveTab('custom')}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                setActiveTab('custom')
              }
            }}
            className="p-6 rounded-lg border-2 border-dashed border-gray-300 hover:border-gray-400 cursor-pointer dark:border-gray-700 dark:hover:border-gray-600"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3 dark:bg-gray-800">
                <FileJson className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </div>
              <h3 className="font-medium text-gray-900 dark:text-white">Create Custom Test</h3>
              <p className="text-sm text-gray-600 mt-1 dark:text-gray-400">Define your own test cases</p>
            </div>
          </div>
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className={`p-6 rounded-lg border-2 ${
            result.can_deploy 
              ? 'bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-900' 
              : 'bg-red-50 border-red-200 dark:bg-red-950/20 dark:border-red-900'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {result.can_deploy ? (
                  <CheckCircle className="w-10 h-10 text-green-600 dark:text-green-400" />
                ) : (
                  <AlertTriangle className="w-10 h-10 text-red-600 dark:text-red-400" />
                )}
                
                <div>
                  <h3 className="text-xl font-semibold dark:text-white">
                    {result.can_deploy ? 'Ready to Deploy' : 'Deployment Blocked'}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {result.passed} passed, {result.failed} failed ({result.pass_rate.toFixed(1)}%)
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                {/* Export Report — hidden (coming soon) */}
              </div>
            </div>

            {result.critical_failures.length > 0 && (
              <div className="mt-4 p-3 bg-red-100 rounded-lg dark:bg-red-950/30">
                <p className="text-red-800 font-medium dark:text-red-400">
                  ⚠️ Critical failures detected - deployment will be blocked
                </p>
                <p className="text-sm text-red-700 mt-1 dark:text-red-300">
                  Failed tests: {result.critical_failures.join(', ')}
                </p>
              </div>
            )}
          </div>

          {/* Test Results List */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden dark:bg-gray-900 dark:border-gray-700">
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {result.results.map((r, idx) => (
                <div key={idx} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {r.passed ? (
                        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 dark:text-green-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600 mt-0.5 dark:text-red-400" />
                      )}
                      
                      <div>
                        <p className="font-medium dark:text-white">{r.test_case.name}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{r.test_case.description}</p>
                        
                        <div className="flex items-center gap-2 mt-2">
                          {r.test_case.tags.map((tag) => (
                            <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded dark:bg-gray-800 dark:text-gray-300">
                              {tag}
                            </span>
                          ))}
                          {r.test_case.critical && (
                            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded font-medium dark:bg-red-950/30 dark:text-red-400">
                              CRITICAL
                            </span>
                          )}
                        </div>

                        {!r.passed && r.error_message && (
                          <p className="text-sm text-red-600 mt-2 dark:text-red-400">
                            {r.error_message}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <p className={`text-sm font-medium ${r.passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {r.actual_action.toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Expected: {r.test_case.expected_action.toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">
                        {r.execution_time_ms}ms
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'results' && !result && (
        <div className="text-center py-12 text-gray-400 dark:text-gray-600">
          <p>Run tests to see results here</p>
        </div>
      )}

      {/* Custom Tests Tab */}
      {activeTab === 'custom' && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 mb-4 dark:text-white">Custom Test Configuration</h3>
          
          <p className="text-gray-600 dark:text-gray-400">Create custom test cases using JSON format:</p>
          
          <pre className="mt-4 p-4 bg-gray-50 rounded-lg text-sm overflow-x-auto dark:bg-gray-950 dark:text-gray-300">
{`{
  "name": "My Custom Test",
  "packet": {
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "protocol": "tcp",
    "dst_port": 8080
  },
  "expected_action": "accept",
  "critical": true
}`}
          </pre>
        </div>
      )}
    </div>
  )
}
