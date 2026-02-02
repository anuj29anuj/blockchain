import hashlib
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

class Block:
    def __init__(self, block_no, nonce, data, prev_hash):
        self.block_no = block_no
        self.nonce = nonce
        self.data = data
        self.prev_hash = prev_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "block_no": self.block_no,
            "nonce": self.nonce,
            "data": self.data,
            "prev_hash": self.prev_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "block_no": self.block_no,
            "nonce": self.nonce,
            "data": self.data,
            "prev_hash": self.prev_hash,
            "hash": self.hash
        }

    def mine_block(self, difficulty=4):
        """Finds a nonce such that the hash starts with 'difficulty' zeros."""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash

@app.route('/mine_block', methods=['POST'])
def mine_block():
    data = request.json
    i = int(data['index'])
    
    # Reset nonce and mine
    blockchain[i].nonce = 0 
    blockchain[i].mine_block(difficulty=4)
    
    return jsonify([b.to_dict() for b in blockchain])

@app.route('/validate', methods=['GET'])
def validate_chain():
    """Checks if any block's prev_hash matches the previous block's hash."""
    validation_results = []
    for i in range(len(blockchain)):
        is_valid = True
        # 1. Check if hash matches content
        if blockchain[i].hash != blockchain[i].calculate_hash():
            is_valid = False
        # 2. Check if link to previous is broken
        if i > 0 and blockchain[i].prev_hash != blockchain[i-1].hash:
            is_valid = False
            
        validation_results.append({"index": i, "valid": is_valid})
    
    return jsonify(validation_results)

blockchain = []

def init_blockchain():
    global blockchain
    blockchain = []
    prev_hash = "0" * 64
    for i in range(1, 6):
        block = Block(i, 0, f"Data for block {i}", prev_hash)
        blockchain.append(block)
        prev_hash = block.hash

init_blockchain()

@app.route('/')
def index():
    return render_template('index.html', blockchain=[b.to_dict() for b in blockchain])

@app.route('/update_block', methods=['POST'])
def update_block():
    data = request.json
    i = int(data['index'])

    blockchain[i].data = data['data']
    blockchain[i].nonce = int(data['nonce'])

    # Recalculate ONLY this block
    blockchain[i].hash = blockchain[i].calculate_hash()

    return jsonify([b.to_dict() for b in blockchain])

@app.route('/propagate', methods=['POST'])
def propagate():
    data = request.json
    start = int(data['index'])

    for i in range(start + 1, len(blockchain)):
        blockchain[i].prev_hash = blockchain[i - 1].hash
        blockchain[i].hash = blockchain[i].calculate_hash()

    return jsonify([b.to_dict() for b in blockchain])


@app.route('/update', methods=['POST'])
def update():
    data = request.json
    block_index = int(data['index'])
    new_data = data['data']
    new_nonce = int(data.get('nonce', blockchain[block_index].nonce))
    
    blockchain[block_index].data = new_data
    blockchain[block_index].nonce = new_nonce
    
    # Recalculate from this block onwards
    for i in range(block_index, len(blockchain)):
        if i > block_index:
            blockchain[i].prev_hash = blockchain[i-1].hash
        elif i == 0:
            # Genesis block prev_hash remains the same
            pass
        
        blockchain[i].hash = blockchain[i].calculate_hash()
        
    return jsonify([b.to_dict() for b in blockchain])

if __name__ == '__main__':
    app.run(debug=True, port=5001)
