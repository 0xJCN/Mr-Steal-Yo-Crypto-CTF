# @version ^0.3.7

TYPE_HASH: constant(bytes32) = keccak256("SendFundsWithAuth(uint256 amount,uint256 nonce)")

@external
@pure
def get_calldata(_to: address, _value: uint256, _data: Bytes[32]) -> Bytes[164]:
    return _abi_encode(_to, _value, _data, method_id=method_id("execute(address,uint256,bytes)"))

@external
@view
def get_permit_hash(domain_separator: bytes32, amount: uint256, nonce: uint256) -> bytes32:
    struct_hash: bytes32 = keccak256(_abi_encode(TYPE_HASH, amount, nonce))

    permit_hash: bytes32 = keccak256(concat(b"\x19\x01", domain_separator, struct_hash))

    return permit_hash

