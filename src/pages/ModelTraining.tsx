import React, { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { useApp } from '../App'

const generateTrainingData = () => {
  const data = []
  let trainLoss = 0.6
  let valLoss = 0.62
  for (let epoch = 1; epoch <= 50; epoch++) {
    trainLoss = Math.max(0.03, trainLoss - (0.01 + Math.random() * 0.008))
    valLoss = Math.max(0.05, valLoss - (0.009 + Math.random() * 0.007))
    data.push({ epoch, trainLoss: +trainLoss.toFixed(4), valLoss: +valLoss.toFixed(4) })
  }
  return data
}

type Architecture = 'LSTM' | 'GRU' | 'Random Forest'

const archMetrics: Record<Architecture, { mae: string; rmse: string; r2: string; acc: string }> = {
  'LSTM':         { mae: '0.042', rmse: '0.118', r2: '0.967', acc: '94.2%' },
  'GRU':          { mae: '0.051', rmse: '0.131', r2: '0.954', acc: '92.8%' },
  'Random Forest':{ mae: '0.068', rmse: '0.159', r2: '0.921', acc: '88.5%' },
}

export default function ModelTraining() {
  const { toast } = useApp()
  const [arch, setArch] = useState<Architecture>('LSTM')
  const [epochs, setEpochs] = useState(50)
  const [batchSize, setBatchSize] = useState(32)
  const [learningRate, setLearningRate] = useState(0.001)
  const [trainingData, setTrainingData] = useState(generateTrainingData())
  const [isTraining, setIsTraining] = useState(false)
  const [displayedEpoch, setDisplayedEpoch] = useState(50)

  const handleTrain = () => {
    setIsTraining(true)
    setDisplayedEpoch(0)
    toast(`Starting ${arch} training (${epochs} epochs)...`, 'info')
    const newData = generateTrainingData()
    setTrainingData(newData)
    let ep = 0
    const interval = setInterval(() => {
      ep += 1
      setDisplayedEpoch(ep)
      if (ep >= epochs) {
        clearInterval(interval)
        setIsTraining(false)
        setDisplayedEpoch(epochs)
        toast(`${arch} training complete! Accuracy: ${archMetrics[arch].acc}`, 'success')
      }
    }, 60)
  }

  const shownData = trainingData.slice(0, displayedEpoch)

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Model Training</h1>
        <p className="text-sm text-gray-400 mt-1">Configure and train traffic prediction models.</p>
      </div>

      <div className="flex gap-4 items-start">
        {/* Config panel */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 w-64 flex-shrink-0 space-y-5">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wide">Model Architecture</p>
            <div className="flex gap-1.5 flex-wrap">
              {(['LSTM', 'GRU', 'Random Forest'] as Architecture[]).map((a) => (
                <button
                  key={a}
                  onClick={() => setArch(a)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    arch === a
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold text-gray-500 mb-4 uppercase tracking-wide">Training Parameters</p>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-xs text-gray-600">Epochs</label>
                  <span className="text-xs font-semibold text-gray-800">{epochs}</span>
                </div>
                <input type="range" min={10} max={100} value={epochs} onChange={e => setEpochs(+e.target.value)} />
              </div>
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-xs text-gray-600">Batch Size</label>
                  <span className="text-xs font-semibold text-gray-800">{batchSize}</span>
                </div>
                <input type="range" min={8} max={128} step={8} value={batchSize} onChange={e => setBatchSize(+e.target.value)} />
              </div>
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-xs text-gray-600">Learning Rate</label>
                  <span className="text-xs font-semibold text-gray-800">{learningRate.toFixed(4)}</span>
                </div>
                <input type="range" min={0.0001} max={0.01} step={0.0001} value={learningRate} onChange={e => setLearningRate(+e.target.value)} />
              </div>
            </div>
          </div>

          <button
            onClick={handleTrain}
            disabled={isTraining}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-60 shadow-sm"
          >
            {isTraining ? `Training... ${displayedEpoch}/${epochs}` : 'Initialize Training'}
          </button>

          {/* Training progress bar */}
          {isTraining && (
            <div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-200"
                  style={{ width: `${(displayedEpoch / epochs) * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 text-center mt-1.5">
                {Math.round((displayedEpoch / epochs) * 100)}% complete
              </p>
            </div>
          )}
        </div>

        {/* Chart */}
        <div className="flex-1 space-y-4">
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900">Training Progress</h2>
            <p className="text-xs text-gray-400 mt-0.5 mb-4">Loss convergence over epochs</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={shownData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="epoch" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 0.65]} tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Line type="monotone" dataKey="trainLoss" name="Training Loss" stroke="#6366f1" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="valLoss" name="Validation Loss" stroke="#9ca3af" strokeWidth={2} dot={false} strokeDasharray="5 4" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'MAE',      value: archMetrics[arch].mae  },
              { label: 'RMSE',     value: archMetrics[arch].rmse },
              { label: 'R² Score', value: archMetrics[arch].r2   },
              { label: 'Accuracy', value: archMetrics[arch].acc  },
            ].map((m) => (
              <div key={m.label} className="bg-white rounded-2xl border border-gray-100 p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">{m.label}</p>
                <p className="text-xl font-bold text-gray-900">{m.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
