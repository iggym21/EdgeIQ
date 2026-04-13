export default function ChatSidebar({ propData, onClose }) {
  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-gray-900 border-l
                    border-gray-800 p-4 z-10">
      <button onClick={onClose} className="text-gray-500 hover:text-gray-300 mb-4">✕</button>
      <p className="text-gray-400 text-sm">Chat — coming in Phase 3</p>
    </div>
  )
}
