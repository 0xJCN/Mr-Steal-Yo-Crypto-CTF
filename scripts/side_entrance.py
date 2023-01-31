from ape import accounts, project
from .utils.helper import MAX_UINT256, w3, get_timestamp

INITIAL_LIQUIDITY = w3.to_wei(1_000_000, "ether")
ADMIN_USDC_TOKENS = w3.to_wei(2_000_000, "ether")
ADMIN_USER_USDC_TOKENS = w3.to_wei(100_000, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]
    admin_user_2 = accounts.test_accounts[3]

    print(
        f"\n--- \nOur players:\n⇒ Attacker: {attacker}\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n⇒ Admin User 2: {admin_user_2}\n---\n"
    )

    # deploy token contracts
    print("\n--- Deploying Token Contracts ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    usdc.mintPerUser(
        [admin.address, admin_user.address],
        [ADMIN_USDC_TOKENS, ADMIN_USER_USDC_TOKENS],
        sender=admin,
    )
    dai = project.Token.deploy("DAI", "DAI", sender=admin)
    dai.mintPerUser(
        [admin.address],
        [INITIAL_LIQUIDITY],
        sender=admin,
    )

    # deploy uniswap contracts
    print("\n--- Deploying Uniswap Contracts ---\n")
    weth = project.WETH9.deploy(sender=admin)
    weth.deposit(value=w3.to_wei(500, "ether"), sender=admin)
    weth.deposit(value=w3.to_wei(50, "ether"), sender=admin_user_2)

    factory = project.UniswapV2Factory.deploy(admin.address, sender=admin)
    router = project.UniswapV2Router02.deploy(
        factory.address, weth.address, sender=admin
    )

    # creating pair and adding initial liquidity
    print("\n--- Creating Pair and adding liquidity ---\n")
    usdc.approve(router.address, MAX_UINT256, sender=admin)
    dai.approve(router.address, MAX_UINT256, sender=admin)
    weth.approve(router.address, MAX_UINT256, sender=admin)

    router.addLiquidity(  # creates USDC-DAI pair
        usdc.address,
        dai.address,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY,
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    usdc_dai_pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, dai.address))

    router.addLiquidity(  # creates USDC-ETH pair
        usdc.address,
        weth.address,
        INITIAL_LIQUIDITY,
        w3.to_wei(500, "ether"),
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    usdc_eth_pair = project.UniswapV2Pair.at(
        factory.getPair(usdc.address, weth.address)
    )

    # Deploying core contracts
    print("\n--- Deploying Core Contracts ---\n")
    options_contract = project.CallOptions.deploy(
        usdc.address,
        weth.address,
        usdc_eth_pair.address,
        factory.address,
        router.address,
        sender=admin,
    )
    # --initial interactions with core contracts
    print("\n--- Simulating initial interactions with core contracts ---\n")
    weth.approve(options_contract.address, MAX_UINT256, sender=admin_user_2)
    expiry_time = get_timestamp() + (60 * 60 * 24 * 7)
    options_contract.createOption(
        w3.to_wei(1, "ether"),
        w3.to_wei(2100, "ether"),
        w3.to_wei(100, "ether"),
        expiry_time,
        sender=admin_user_2,
    )
    created_option_id = options_contract.getLatestOptionId()
    usdc.approve(options_contract.address, MAX_UINT256, sender=admin_user)
    options_contract.purchaseOption(created_option_id, sender=admin_user)

    # define initial balance for attacker
    attacker_initial_bal = usdc.balanceOf(attacker.address) / 10**18

    print(f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n---\n")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker stole at least 90k USDC ---\n")

    # define ending balance for attacker
    attacker_ending_bal = usdc.balanceOf(attacker.address) / 10**18

    print(f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n---\n")

    # attacker steals at least 90k USDC

    assert usdc.balanceOf(attacker.address) >= w3.to_wei(90_000, "ether")

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
