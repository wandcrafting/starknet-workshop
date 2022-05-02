%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.math import assert_le

struct Star:
    member name : felt
    member size : felt
end

@storage_var
func dust(address : felt) -> (amount : felt):
end

@storage_var
func star(address : felt, slot : felt) -> (star : Star):
end

@storage_var
func slot(address : felt) -> (slot : felt):
end

@event
func a_star_is_born(account : felt, slot : felt, size : Star):
end

@external
func collect_dust{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(amount : felt):
    let (address) = get_caller_address()

    let (res) = dust.read(address)
    dust.write(address, res + amount)

    return ()
end

@external
func light_star{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        star_struct : Star):
    
    let (address) = get_caller_address()

    let (dust_owned) = dust.read(address)
    assert_le(star_struct.size, dust_owned)

    let (next_slot) = slot.read(address)
    
    dust.write(address, dust_owned - star_struct.size)
    star.write(address, next_slot, star_struct)
    slot.write(address, next_slot + 1)

    a_star_is_born.emit(account=address, slot=next_slot, size=star_struct)
    return ()
end


@view
func view_dust{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        address : felt) -> (amount : felt):
    let (res) = dust.read(address)
    return (res)
end

@view
func view_star{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        address : felt, slot : felt) -> (star : Star):
    let (res) = star.read(address, slot)
    return (res)
end

@view
func view_slot{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        address : felt) -> (amount : felt):
    let (res) = slot.read(address)
    return (res)
end
