import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Shield, Server, Users, Activity } from 'lucide-react'

const protocolIcons: Record<string, string> = {
  wireguard: '⚡',
  ipsec: '🔒',
  openvpn: '🛡️',
  l2tp: '📡',
  pptp: '⚠️',
}

const protocolColors: Record<string, string> = {
  wireguard: 'bg-green-100 text-green-800',
  ipsec: 'bg-blue-100 text-blue-800',
  openvpn: 'bg-yellow-100 text-yellow-800',
  l2tp: 'bg-orange-100 text-orange-800',
  pptp: 'bg-red-100 text-red-800',
}

// Mock data for now
const mockServers = [
  {
    id: 1,
    name: 'Main Office VPN',
    protocol: 'wireguard',
    status: 'running',
    listen_port: 51820,
    network_cidr: '10.200.0.0/24',
    connected_clients: 12,
    total_bytes: '1.2 GB',
  },
  {
    id: 2,
    name: 'Legacy IPsec',
    protocol: 'ipsec',
    status: 'running',
    listen_port: 500,
    network_cidr: '10.201.0.0/24',
    connected_clients: 5,
    total_bytes: '450 MB',
  },
]

export function VPNServers() {
  const [servers] = useState(mockServers)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">VPN Servers</h2>
          <p className="text-gray-600 mt-1">Manage WireGuard, IPsec, OpenVPN, and legacy protocols</p>
        </div>
        <Link
          to="/vpn/create"
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          New VPN Server
        </Link>
      </div>

      {/* Protocol Recommendations */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg mb-6 border border-blue-100">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Shield className="w-6 h-6 text-blue-700" />
          </div>
          <div>
            <h3 className="font-semibold text-blue-900">Recommended: WireGuard</h3>
            <p className="text-blue-800 text-sm mt-1">
              Modern, fast, and secure. WireGuard uses state-of-the-art cryptography 
              and is recommended for all new deployments.
            </p>
            <div className="flex gap-4 mt-3">
              <span className="text-xs bg-blue-200 text-blue-900 px-2 py-1 rounded">⚡ High Performance</span>
              <span className="text-xs bg-blue-200 text-blue-900 px-2 py-1 rounded">🔐 Modern Crypto</span>
              <span className="text-xs bg-blue-200 text-blue-900 px-2 py-1 rounded">📱 Mobile Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* Servers List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {servers.length === 0 ? (
          <div className="p-12 text-center">
            <Server className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No VPN servers</h3>
            <p className="text-gray-600 mb-6">Create your first VPN server to enable remote access.</p>
            <Link
              to="/vpn/create"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Create VPN Server
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {servers.map((server) => (
              <Link
                key={server.id}
                to={`/vpn/servers/${server.id}`}
                className="p-6 hover:bg-gray-50 flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${protocolColors[server.protocol]}`}>
                    <span className="text-xl">{protocolIcons[server.protocol]}</span>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">{server.name}</h3>
                    <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                      <span className="capitalize">{server.protocol}</span>
                      <span>•</span>
                      <span>Port {server.listen_port}</span>
                      <span>•</span>
                      <span>{server.network_cidr}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Users className="w-4 h-4" />
                    {server.connected_clients} connected
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Activity className="w-4 h-4" />
                    {server.total_bytes}
                  </div>
                  
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    server.status === 'running'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {server.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
