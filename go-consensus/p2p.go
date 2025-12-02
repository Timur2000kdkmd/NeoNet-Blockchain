package main

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

type WireMessage struct {
	Type string          `json:"type"`
	Body json.RawMessage `json:"body,omitempty"`
	From string          `json:"from,omitempty"`
}

type PeerListBody struct {
	Peers []string `json:"peers"`
}

type TxBody struct {
	Data string `json:"data"`
}

type ChainBody struct {
	Chain []*Block `json:"chain"`
}

type Node struct {
	cfg     Config
	peersMu sync.RWMutex
	peers   map[string]struct{}
	ln      net.Listener
	bc      *Blockchain
	logger  *log.Logger
}

type Config struct {
	Port  string
	Peers string
}

func NewNode(cfg Config) *Node {
	n := &Node{
		cfg:    cfg,
		peers:  make(map[string]struct{}),
		bc:     NewBlockchain(),
		logger: log.Default(),
	}
	if cfg.Peers != "" {
		for _, p := range strings.Split(cfg.Peers, ",") {
			p = strings.TrimSpace(p)
			if p != "" {
				n.peers[p] = struct{}{}
			}
		}
	}
	if len(n.bc.chain) == 0 {
		n.bc.CreateGenesis()
	}
	return n
}

func (n *Node) Start() {
	addr := fmt.Sprintf(":%s", n.cfg.Port)
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		n.logger.Fatalf("listen: %v", err)
	}
	n.ln = ln
	n.logger.Printf("P2P listening on %s", addr)

	go n.connectToInitialPeers()

	for {
		conn, err := ln.Accept()
		if err != nil {
			n.logger.Printf("accept error: %v", err)
			continue
		}
		go n.handleConn(conn)
	}
}

func (n *Node) connectToInitialPeers() {
	n.peersMu.RLock()
	plist := make([]string, 0, len(n.peers))
	for p := range n.peers {
		plist = append(plist, p)
	}
	n.peersMu.RUnlock()

	for _, p := range plist {
		go n.connectAndHandshake(p)
	}
}

func (n *Node) connectAndHandshake(peerAddr string) {
	conn, err := net.DialTimeout("tcp", peerAddr, 3*time.Second)
	if err != nil {
		n.logger.Printf("connect %s error: %v", peerAddr, err)
		return
	}
	n.logger.Printf("connected to %s", peerAddr)
	pl := n.getPeerList()
	body, _ := json.Marshal(PeerListBody{Peers: pl})
	msg := WireMessage{Type: "peerList", Body: body, From: ":" + n.cfg.Port}
	enc := json.NewEncoder(conn)
	if err := enc.Encode(&msg); err != nil {
		n.logger.Printf("handshake send error to %s: %v", peerAddr, err)
		conn.Close()
		return
	}
	req := WireMessage{Type: "requestChain", From: ":" + n.cfg.Port}
	_ = enc.Encode(&req)
	n.handleConn(conn)
}

func (n *Node) handleConn(conn net.Conn) {
	defer conn.Close()
	remote := conn.RemoteAddr().String()
	n.addPeer(remote)
	dec := json.NewDecoder(conn)
	enc := json.NewEncoder(conn)
	for {
		var msg WireMessage
		if err := dec.Decode(&msg); err != nil {
			return
		}
		switch msg.Type {
		case "peerList":
			var pl PeerListBody
			_ = json.Unmarshal(msg.Body, &pl)
			for _, p := range pl.Peers {
				if p != "" {
					n.addPeer(p)
				}
			}
			my := n.getPeerList()
			b, _ := json.Marshal(PeerListBody{Peers: my})
			_ = enc.Encode(WireMessage{Type: "peerList", Body: b, From: ":" + n.cfg.Port})
		case "tx":
			var tx TxBody
			_ = json.Unmarshal(msg.Body, &tx)
			n.logger.Printf("received tx: %s", tx.Data)
			newB := n.bc.GenerateBlock(tx.Data)
			if n.bc.AddBlock(newB) {
				n.logger.Printf("added block %d", newB.Index)
				go postBlockToAI(newB)
				n.broadcastBlock(newB)
			}
		case "block":
			var b Block
			_ = json.Unmarshal(msg.Body, &b)
			n.logger.Printf("received block %d", b.Index)
			if VerifyBlockSignature(&b) {
				if n.bc.AddBlock(&b) {
					n.logger.Printf("added block %d from peer", b.Index)
					go postBlockToAI(&b)
					n.broadcastBlock(&b)
				} else {
					_ = enc.Encode(WireMessage{Type: "requestChain", From: ":" + n.cfg.Port})
				}
			}
		case "requestChain":
			cb, _ := json.Marshal(ChainBody{Chain: n.bc.chain})
			_ = enc.Encode(WireMessage{Type: "chain", Body: cb, From: ":" + n.cfg.Port})
		case "chain":
			var cb ChainBody
			_ = json.Unmarshal(msg.Body, &cb)
			n.logger.Printf("received chain length=%d", len(cb.Chain))
			n.bc.ReplaceChain(cb.Chain)
		}
	}
}

func (n *Node) getPeerList() []string {
	n.peersMu.RLock()
	defer n.peersMu.RUnlock()
	out := make([]string, 0, len(n.peers))
	for p := range n.peers {
		out = append(out, p)
	}
	return out
}

func (n *Node) addPeer(a string) {
	if a == "" {
		return
	}
	n.peersMu.Lock()
	defer n.peersMu.Unlock()
	if _, ok := n.peers[a]; !ok {
		n.peers[a] = struct{}{}
		n.logger.Printf("added peer %s", a)
	}
}

func (n *Node) broadcastBlock(b *Block) {
	n.peersMu.RLock()
	peers := make([]string, 0, len(n.peers))
	for p := range n.peers {
		peers = append(peers, p)
	}
	n.peersMu.RUnlock()

	body, _ := json.Marshal(b)
	msg := WireMessage{Type: "block", Body: body, From: ":" + n.cfg.Port}
	for _, p := range peers {
		go func(peerAddr string) {
			conn, err := net.DialTimeout("tcp", peerAddr, 2*time.Second)
			if err != nil {
				return
			}
			defer conn.Close()
			enc := json.NewEncoder(conn)
			_ = enc.Encode(msg)
		}(p)
	}
}

func postBlockToAI(b *Block) {
	ai := os.Getenv("AI_BASE")
	if ai == "" {
		ai = "http://127.0.0.1:8000"
	}
	url := ai + "/ingest_block"
	jb, err := json.Marshal(b)
	if err != nil {
		return
	}
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Post(url, "application/json", bytes.NewReader(jb))
	if err != nil {
		return
	}
	resp.Body.Close()
}

func (n *Node) HandleGetChain(w http.ResponseWriter, r *http.Request) {
	n.bc.mu.RLock()
	defer n.bc.mu.RUnlock()
	bts, _ := json.MarshalIndent(n.bc.chain, "", "  ")
	w.Header().Set("Content-Type", "application/json")
	w.Write(bts)
}

func (n *Node) HandleGetPeers(w http.ResponseWriter, r *http.Request) {
	pl := n.getPeerList()
	bts, _ := json.Marshal(pl)
	w.Header().Set("Content-Type", "application/json")
	w.Write(bts)
}

func (n *Node) HandlePostTx(w http.ResponseWriter, r *http.Request) {
	var tb TxBody
	dec := json.NewDecoder(r.Body)
	if err := dec.Decode(&tb); err != nil {
		http.Error(w, "invalid body", http.StatusBadRequest)
		return
	}
	newB := n.bc.GenerateBlock(tb.Data)
	if n.bc.AddBlock(newB) {
		n.bc.SaveToFile("chain_store.json")
		n.broadcastBlock(newB)
		go postBlockToAI(newB)
		w.WriteHeader(http.StatusCreated)
		b, _ := json.Marshal(newB)
		w.Write(b)
		return
	}
	http.Error(w, "failed to add block", http.StatusInternalServerError)
}

func (n *Node) LoadChainFromFile(fn string) error {
	if n.bc == nil {
		n.bc = NewBlockchain()
	}
	err := n.bc.LoadFromFile(fn)
	if err != nil {
		return err
	}
	n.logger.Printf("loaded chain from %s length=%d", fn, len(n.bc.chain))
	return nil
}

func (n *Node) HandleRelayExecute(w http.ResponseWriter, r *http.Request) {
	var in map[string]interface{}
	dec := json.NewDecoder(r.Body)
	if err := dec.Decode(&in); err != nil {
		http.Error(w, "invalid body", http.StatusBadRequest)
		return
	}
	mock := os.Getenv("COSMWASM_MOCK")
	if mock == "" {
		mock = "http://127.0.0.1:8001"
	}
	bts, _ := json.Marshal(in)
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Post(mock+"/execute", "application/json", bytes.NewReader(bts))
	if err != nil {
		http.Error(w, "relay error: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()
	out, _ := io.ReadAll(resp.Body)
	w.Write(out)
}

var voteLock sync.Mutex
var votesMap = make(map[string]map[string]Vote)

type Vote struct {
	BlockHash string `json:"block_hash"`
	VoterPub  string `json:"voter_pub"`
	Signature string `json:"signature"`
	Round     int    `json:"round"`
}

func (n *Node) HandleVote(w http.ResponseWriter, r *http.Request) {
	var v Vote
	dec := json.NewDecoder(r.Body)
	if err := dec.Decode(&v); err != nil {
		http.Error(w, "invalid vote", http.StatusBadRequest)
		return
	}
	pubb, err := hex.DecodeString(v.VoterPub)
	if err != nil {
		http.Error(w, "bad pub", http.StatusBadRequest)
		return
	}
	sigb, err := hex.DecodeString(v.Signature)
	if err != nil {
		http.Error(w, "bad sig", http.StatusBadRequest)
		return
	}
	msg := []byte(fmt.Sprintf("%s:%d", v.BlockHash, v.Round))
	if !ed25519.Verify(ed25519.PublicKey(pubb), msg, sigb) {
		http.Error(w, "invalid signature", http.StatusBadRequest)
		return
	}
	voteLock.Lock()
	defer voteLock.Unlock()
	if votesMap[v.BlockHash] == nil {
		votesMap[v.BlockHash] = make(map[string]Vote)
	}
	votesMap[v.BlockHash][v.VoterPub] = v
	validators := n.getValidatorList()
	needed := (2*len(validators))/3 + 1
	count := len(votesMap[v.BlockHash])
	if count >= needed {
		n.logger.Printf("block %s committed by %d/%d votes", v.BlockHash, count, len(validators))
	}
	w.Write([]byte(fmt.Sprintf(`{"ok":true,"votes":%d}`, count)))
}

func (n *Node) getValidatorList() []string {
	var out []string
	data, err := os.ReadFile("validators.json")
	if err == nil {
		_ = json.Unmarshal(data, &out)
		if len(out) > 0 {
			return out
		}
	}
	out = n.getPeerList()
	return out
}

func (n *Node) HandlePBFTPrePrepare(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"ok":true}`))
}

func (n *Node) HandlePBFTPrepare(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"ok":true}`))
}

func (n *Node) HandlePBFTCommit(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"ok":true}`))
}
