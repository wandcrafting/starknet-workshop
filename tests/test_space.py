from typing import List, NamedTuple
import pytest

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name

from fixtures import *
from deploy import deploy_contract
from utils import assert_revert, to_uint

ADMIN = get_selector_from_name('admin')
ANYONE = get_selector_from_name('anyone')
SPACE_SIZE = 6
MAX_TURN = 50
MAX_DUST = 2
MAX_FELT = 2**251 + 17 * 2**192 + 1

@pytest.fixture
async def space_factory(starknet: Starknet) -> StarknetContract:
    rand = await deploy_contract(starknet, 'test/fake_rand.cairo')
    space = await deploy_contract(starknet, 'core/space.cairo')
    dust = await deploy_contract(starknet, 'core/dust.cairo', constructor_calldata=[space.contract_address, rand.contract_address])
    await space.initialize(dust.contract_address, SPACE_SIZE, MAX_TURN, MAX_DUST).invoke(caller_address=ADMIN)
    return space, dust


@pytest.mark.asyncio
async def test_turn_count(starknet: Starknet):
    rand = await deploy_contract(starknet, 'test/fake_rand.cairo')
    space = await deploy_contract(starknet, 'core/space.cairo')
    dust = await deploy_contract(starknet, 'core/dust.cairo', constructor_calldata=[space.contract_address, rand.contract_address])

    MAX_TURN = 2
    await space.initialize(dust.contract_address, SPACE_SIZE, MAX_TURN, MAX_DUST).invoke(caller_address=ADMIN)

    execution_info = await space.get_max_turn_count().call()
    assert execution_info.result.count == MAX_TURN
    execution_info = await space.get_current_turn().call()
    assert execution_info.result.num == 0

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    execution_info = await space.get_current_turn().call()
    assert execution_info.result.num == 1

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    execution_info = await space.get_current_turn().call()
    assert execution_info.result.num == 2

    # Next turn --------------------------------------------------
    await assert_revert(space.next_turn().invoke(caller_address=ADMIN))

@pytest.mark.asyncio
async def test_next_turn_no_ship(space_factory):
    space, dust = space_factory

    # Assert grid is empty
    await assert_grid_state(space, [])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 1), Vector2(0, 1))
    await assert_grid_state(space, [Cell(Vector2(0, 1), 1, 0)])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 2), Vector2(0, 1))
    await assert_dust_state(dust, 2, Vector2(0, 4), Vector2(0, -1))
    await assert_grid_state(space, [Cell(Vector2(0, 2), 1, 0), Cell(Vector2(0, 4), 2, 0)])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 3), Vector2(0, 1))
    await assert_dust_state(dust, 2, Vector2(0, 3), Vector2(0, -1))
    # MAX_DUST == 2 so no more dust has been spawned

    # A collision occured, assert the dust was burnt
    await assert_revert(dust.ownerOf(to_uint(2)).call(), reverted_with='ERC721: owner query for nonexistent token')

    await assert_grid_state(space, [Cell(Vector2(0, 3), 1, 0)])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 4), Vector2(0, 1))
    # a new dust was spawned, with the id of the burnt token
    await assert_dust_state(dust, 2, Vector2(5, 1), Vector2(0, 1))

    await assert_grid_state(space, [Cell(Vector2(0, 4), 1, 0), Cell(Vector2(5, 1), 2, 0)])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 5), Vector2(0, 1))
    await assert_dust_state(dust, 2, Vector2(5, 2), Vector2(0, 1))
    # no new dust was spawned, because it would have been at the same position (5,2)

    await assert_grid_state(space, [Cell(Vector2(0, 5), 1, 0), Cell(Vector2(5, 2), 2, 0)])


@pytest.mark.asyncio
async def test_add_ship(starknet: Starknet, space_factory):
    space, _ = space_factory
    ship1 = await deploy_contract(starknet, 'ships/static_ship.cairo')
    ship2 = await deploy_contract(starknet, 'ships/static_ship.cairo')

    await space.add_ship(3, 3, ship1.contract_address).invoke(caller_address=ADMIN)
    await assert_grid_state(space, [Cell(Vector2(3, 3), 0, 1)])

    await assert_revert(space.add_ship(3, 3, ship2.contract_address).invoke(caller_address=ADMIN))


@pytest.mark.asyncio
async def test_next_turn_with_ship(starknet: Starknet, space_factory):
    space, dust = space_factory
    ship: StarknetContract = await deploy_contract(starknet, 'ships/static_ship.cairo')
    await space.add_ship(0, 3, ship.contract_address).invoke(caller_address=ADMIN)
    ship_assertion = Cell(Vector2(0, 3), 0, 1)

    # Assert grid is empty
    await assert_grid_state(space, [ship_assertion])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 1), Vector2(0, 1))
    await assert_grid_state(space, [Cell(Vector2(0, 1), 1, 0), ship_assertion])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 2), Vector2(0, 1))
    await assert_dust_state(dust, 2, Vector2(0, 4), Vector2(0, -1))
    await assert_grid_state(space, [Cell(Vector2(0, 2), 1, 0), Cell(Vector2(0, 4), 2, 0), ship_assertion])

    # Assert the space owns the dusts
    execution_info = await dust.ownerOf(to_uint(1)).call()
    assert execution_info.result == (space.contract_address,)
    execution_info = await dust.ownerOf(to_uint(2)).call()
    assert execution_info.result == (space.contract_address,)

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 1, Vector2(0, 3), Vector2(0, 1))
    await assert_dust_state(dust, 2, Vector2(0, 3), Vector2(0, -1))
    # MAX_DUST == 2 so no more dust has been spawned

    # Assert the ship earned the dusts at position (0, 3)
    execution_info = await dust.ownerOf(to_uint(1)).call()
    assert execution_info.result == (ship.contract_address,)
    execution_info = await dust.ownerOf(to_uint(2)).call()
    assert execution_info.result == (ship.contract_address,)

    await assert_grid_state(space, [ship_assertion])

    # Next turn --------------------------------------------------
    await space.next_turn().invoke(caller_address=ADMIN)

    await assert_dust_state(dust, 3, Vector2(5, 1), Vector2(0, 1))

    await assert_grid_state(space, [Cell(Vector2(5, 1), 3, 0), ship_assertion])

#
# Helpers to assert the state of the entire grid
#
class Vector2(NamedTuple):
    x: int
    y: int

class Cell(NamedTuple):
    position: Vector2
    dust_id: int
    ship_id: int


async def assert_grid_state(space, cells: List[Cell]):
    execution_info = await space.get_grid_state().call()
    grid_state = execution_info.result.grid_state
    for cell in cells:
        index_in_state = SPACE_SIZE * cell.position.y + cell.position.x
        cell_in_state = grid_state[index_in_state]
        assert cell.dust_id == cell_in_state.dust_id.low
        assert cell.ship_id == cell_in_state.ship_id

async def assert_dust_state(dust, id:int, position:Vector2, direction:Vector2):
    execution_info = await dust.metadata(to_uint(id)).call()
    _, (position_x, position_y), (direction_x, direction_y) = execution_info.result.metadata
    assert position_x == position.x
    assert position_y == position.y
    assert direction_x == direction.x % MAX_FELT
    assert direction_y == direction.y % MAX_FELT
