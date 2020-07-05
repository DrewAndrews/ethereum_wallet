pragma solidity ^0.5.13;

contract registrar {

    mapping(string => address) public base_from_number_to_adddress;
    mapping(address => string) public base_from_address_to_number;

    function create_user(string memory phone_number) public {
        base_from_number_to_adddress[phone_number] = msg.sender;
        base_from_address_to_number[msg.sender] = phone_number;
    }

    function delete_user(string memory phone_number) public {
        base_from_address_to_number[base_from_number_to_adddress[phone_number]] = "";
        base_from_number_to_adddress[phone_number] = 0x0000000000000000000000000000000000000000;
    }

    function get_address(string memory phone_number) public view returns(address) {
        return base_from_number_to_adddress[phone_number];
    }

    function get_number(address user_address) public view returns(bytes memory){
        return bytes(base_from_address_to_number[user_address]);
    }
}