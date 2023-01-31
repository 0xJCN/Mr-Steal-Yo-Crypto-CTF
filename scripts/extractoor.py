from ape import accounts, project
from .utils.helper import get_timestamp, w3

TOKENS_IN_AUCTON_CONTRACT = w3.to_wei(1_000_000, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Attacker: {attacker}\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n---\n"
    )

    # initializing core + periphery auction contracts
    print("\n--- Deploying Core + Periphery Auction Contracts ---\n")
    farm = project.Token.deploy("FARM", "FARM", sender=admin)
    farm.mintPerUser([admin.address], [TOKENS_IN_AUCTON_CONTRACT], sender=admin)

    dutch_auction = project.DutchAuction.deploy(sender=admin)

    farm.approve(dutch_auction.address, TOKENS_IN_AUCTON_CONTRACT, sender=admin)

    dutch_auction.initAuction(
        admin.address,
        farm.address,
        TOKENS_IN_AUCTON_CONTRACT,
        get_timestamp() + 1,
        get_timestamp() + 101,
        w3.to_wei(0.001, "ether"),
        w3.to_wei(0.0005, "ether"),
        admin.address,
        sender=admin,
    )
    # --buying into the auction w/ 900 ETH
    dutch_auction.commitEth(
        admin_user.address, value=w3.to_wei(900, "ether"), sender=admin_user
    )

    # define initial balance for attacker and auction contract
    attacker_initial_bal = attacker.balance / 10**18
    auction_initial_bal = dutch_auction.balance / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Auction: {auction_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After exploit: Attacker drained over 90% of ETH from the contract ---\n"
    )

    # define ending balance for attacker and auction contract
    attacker_ending_bal = attacker.balance / 10**18
    auction_ending_bal = dutch_auction.balance / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Auction: {auction_ending_bal}\n---\n"
    )

    # attacker drains >= 90% ETH from contract
    assert dutch_auction.balance <= w3.to_wei(90, "ether")
    assert (attacker_ending_bal - attacker_initial_bal) >= w3.to_wei(810, "ether")

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
