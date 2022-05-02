%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin, BitwiseBuiltin
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.math import unsigned_div_rem, assert_lt
from starkware.cairo.common.uint256 import Uint256, uint256_add
from starkware.starknet.common.syscalls import get_caller_address

from openzeppelin.token.erc721.library import (
    ERC721_name, ERC721_symbol, ERC721_balanceOf, ERC721_ownerOf, ERC721_isApprovedForAll,
    ERC721_setApprovalForAll, ERC721_initializer)
from openzeppelin.token.erc721_enumerable.library import (
    ERC721_Enumerable_initializer, ERC721_Enumerable_safeTransferFrom, ERC721_Enumerable_mint,
    ERC721_Enumerable_burn, ERC721_Enumerable_totalSupply)

from openzeppelin.introspection.ERC165 import ERC165_supports_interface

from openzeppelin.access.ownable import Ownable_initializer, Ownable_only_owner

from contracts.models.common import Dust, Vector2
from contracts.interfaces.irand import IRandom

#
# Constructor
#

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(owner : felt):
    ERC721_initializer('Dust Non Fungible Token','DUST')
    ERC721_Enumerable_initializer()
    Ownable_initializer(owner)
    return ()
end

#
# Getters
#

@view
func name{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (name : felt):
    let (name) = ERC721_name()
    return (name)
end

@view
func symbol{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (symbol : felt):
    let (symbol) = ERC721_symbol()
    return (symbol)
end

@view
func balanceOf{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(owner : felt) -> (
        balance : Uint256):
    let (balance) = ERC721_balanceOf(owner)
    return (balance)
end

@view
func ownerOf{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        tokenId : Uint256) -> (owner : felt):
    let (owner) = ERC721_ownerOf(tokenId)
    return (owner)
end

@view
func isApprovedForAll{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner : felt, operator : felt) -> (isApproved : felt):
    let (isApproved) = ERC721_isApprovedForAll(owner, operator)
    return (isApproved)
end

#
# Externals
#

@external
func setApprovalForAll{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        operator : felt, approved : felt):
    ERC721_setApprovalForAll(operator, approved)
    return ()
end

@external
func safeTransferFrom{pedersen_ptr : HashBuiltin*, syscall_ptr : felt*, range_check_ptr}(
        from_ : felt, to : felt, tokenId : Uint256):
    let (data) = alloc()
    ERC721_Enumerable_safeTransferFrom(from_, to, tokenId, 0, data)
    return ()
end

# @external
# func mint{
#         pedersen_ptr : HashBuiltin*, syscall_ptr : felt*, range_check_ptr,
#         bitwise_ptr : BitwiseBuiltin*}(dust : Dust) -> (token_id : Uint256):
#     alloc_locals
#     Ownable_only_owner()
    
#     #to, tokenId, data_len, data
#     #ERC721_Enumerable_mint(dust)
#     let token_id = uint256(3)
#     return ()
# end

@external
func burn{pedersen_ptr : HashBuiltin*, syscall_ptr : felt*, range_check_ptr}(token_id : Uint256):
    Ownable_only_owner()
    ERC721_Enumerable_burn(token_id)
    return ()
end
