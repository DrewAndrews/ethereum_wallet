pragma solidity ^0.5.13;

contract payments {

    mapping(address => bytes32[]) public payments_base;
    
    function add_payment(address user_address, address reciever, bytes32 tx_hash) public {
        payments_base[user_address].push(tx_hash);
        payments_base[reciever].push(tx_hash);
    }
    
    function get_payments_list(address user_address) public view returns(bytes32[] memory) {
        return payments_base[user_address];
    }
}