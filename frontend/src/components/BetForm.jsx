export default function BetForm({ propData, onClose, onSaved }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-30">
      <div className="bg-gray-900 rounded-xl p-6 w-96 border border-gray-700">
        <p className="text-gray-400 text-sm">Bet form — coming in Phase 4</p>
        <button onClick={onClose} className="mt-4 text-gray-500">Close</button>
      </div>
    </div>
  )
}
