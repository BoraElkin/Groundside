import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadPenaltyNotice, createDispute } from '../services/api'
import { DisputeCreateData } from '../types/dispute'

const NewDispute = () => {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'upload' | 'manual'>('upload')
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Manual entry form state
  const [formData, setFormData] = useState<DisputeCreateData>({
    flight_number: '',
    flight_date: '',
    claimed_delay_minutes: 0,
    penalty_amount: 0,
    penalty_currency: 'USD',
    airline_claimed_reason: '',
  })

  const handleFileUpload = async (file: File) => {
    setUploading(true)
    setError(null)

    try {
      // Upload file
      const dispute = await uploadPenaltyNotice(file)

      // Navigate to dispute detail page
      navigate(`/disputes/${dispute.id}`)
    } catch (err: any) {
      console.error('Upload failed:', err)
      setError(err.response?.data?.detail || 'Failed to upload file. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0])
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUploading(true)
    setError(null)

    try {
      const dispute = await createDispute(formData)
      navigate(`/disputes/${dispute.id}`)
    } catch (err: any) {
      console.error('Create failed:', err)
      setError(err.response?.data?.detail || 'Failed to create dispute. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create New Dispute</h1>
        <p className="mt-2 text-gray-600">
          Upload a penalty notice or enter details manually
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="mb-8">
        <div className="flex space-x-4 border-b border-gray-200">
          <button
            onClick={() => setMode('upload')}
            className={`pb-4 px-4 font-medium text-sm border-b-2 ${
              mode === 'upload'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Upload Penalty Notice
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`pb-4 px-4 font-medium text-sm border-b-2 ${
              mode === 'manual'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Manual Entry
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Mode */}
      {mode === 'upload' && (
        <div className="bg-white rounded-lg shadow p-8">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            {uploading ? (
              <div className="space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <div className="text-gray-600">
                  Uploading and extracting details...
                </div>
              </div>
            ) : (
              <>
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <div className="mt-4 text-gray-600">
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 hover:text-blue-700 font-medium">
                      Click to upload
                    </span>
                    <span> or drag and drop</span>
                  </label>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    onChange={handleFileInput}
                    accept=".pdf,.txt,.png,.jpg,.jpeg"
                  />
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  PDF, TXT, PNG, JPG up to 10MB
                </p>
                <p className="mt-4 text-sm text-gray-600">
                  Our AI will automatically extract flight details, delay information,
                  and penalty amounts from your document.
                </p>
              </>
            )}
          </div>
        </div>
      )}

      {/* Manual Entry Mode */}
      {mode === 'manual' && (
        <form onSubmit={handleManualSubmit} className="bg-white rounded-lg shadow p-8">
          <div className="space-y-6">
            {/* Flight Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Flight Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Flight Number *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.flight_number}
                    onChange={(e) =>
                      setFormData({ ...formData, flight_number: e.target.value })
                    }
                    placeholder="e.g. TK1234"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Flight Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.flight_date}
                    onChange={(e) =>
                      setFormData({ ...formData, flight_date: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Delay Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Delay & Penalty Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Claimed Delay (minutes) *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={formData.claimed_delay_minutes === 0 ? '' : formData.claimed_delay_minutes}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        claimed_delay_minutes: e.target.value === '' ? 0 : parseInt(e.target.value),
                      })
                    }
                    placeholder="e.g. 45"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Penalty Amount *
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="number"
                      required
                      min="0"
                      step="0.01"
                      value={formData.penalty_amount === 0 ? '' : formData.penalty_amount}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          penalty_amount: e.target.value === '' ? 0 : parseFloat(e.target.value),
                        })
                      }
                      placeholder="e.g. 5000"
                      className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <select
                      value={formData.penalty_currency}
                      onChange={(e) =>
                        setFormData({ ...formData, penalty_currency: e.target.value })
                      }
                      className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                      <option value="TRY">TRY</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Airline's Claimed Reason */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Airline's Claimed Reason
              </label>
              <textarea
                value={formData.airline_claimed_reason}
                onChange={(e) =>
                  setFormData({ ...formData, airline_claimed_reason: e.target.value })
                }
                rows={3}
                placeholder="e.g. Ground handler caused delay during boarding"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => navigate('/disputes')}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Creating...' : 'Create Dispute'}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  )
}

export default NewDispute
