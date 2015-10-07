"""daytrades: Daytrades plugin for the trade module.

This plugin provides the Daytrade class, a subclass of Operation, and
the fetch_daytrades() task for the OperationContainer.

With this plugin the trade module can:
- Identify daytrades in a group of operations
- Separate daytrades from other operations on the OperationContainer
- Accumulate Daytrades on the portfolio

It provides:
- Daytrade, a subclass of trade.Operation
- the fetch_daytrades() task to the OperationContainer

Daytrades can be accumulated just like any other Operation object.
They will update the accumulated results, but will not change the
quantity or the price of the asset on the Portfolio.

http://trade.readthedocs.org/
https://github.com/rochars/trade
License: MIT

Copyright (c) 2015 Rafael da Silva Rocha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from __future__ import absolute_import

from ..utils import same_sign, merge_operations
from ..trade import Operation


class Daytrade(Operation):
    """A daytrade operation.

    Daytrades are operations of purchase and sale of an Asset on
    the same date.

    Attributes:
        asset: An asset instance, the asset that is being traded.
        quantity: The traded quantity of the asset.
        purchase: A Operation object representing the purchase of the
            asset.
        sale: A Operation object representing the sale of the asset.
        update_position: Set to False, as daytrades don't change the
            portfolio position; they just create results.
    """

    update_position = False

    def __init__(self, operation_a, operation_b):
        """Creates the daytrade object.

        Base on the informed values this method creates 2 operations:
        - a purchase operation
        - a sale operation
        and them appends them to the Daytrade object operations list.

        Both operations can be treated like any other operation when it
        comes to taxes and the prorate of commissions.
        """
        super(Daytrade, self).__init__(
            date=operation_a.date,
            asset=operation_a.asset,
        )
        purchase, sale = find_purchase_and_sale(operation_a, operation_b)
        self.extract_daytrade(purchase, sale)

        # Purchase is 0, Sale is 1
        self.operations = [
            Operation(
                date=purchase.date,
                asset=purchase.asset,
                quantity=self.quantity,
                price=purchase.price
            ),
            Operation(
                date=sale.date,
                asset=sale.asset,
                quantity=self.quantity*-1,
                price=sale.price
            )
        ]

    @property
    def results(self):
        """Returns the profit or the loss generated by the daytrade."""
        return {
            'daytrades': abs(self.operations[1].real_value) - \
                                        abs(self.operations[0].real_value)
        }

    def extract_daytrade(self, purchase, sale):
        """Extract the daytraded quantity from 2 operations.

        Returns the daytraded quantity.
        """
        # Find the daytraded quantity; the daytraded
        # quantity is always the smallest absolute quantity
        self.quantity = min([abs(purchase.quantity), abs(sale.quantity)])

        # Update the operations that originated the
        # daytrade with the new quantity after the
        # daytraded part has been extracted; One of
        # the operations will always have zero
        # quantity after this, being fully consumed
        # by the daytrade. The other operation may or
        # may not end with zero quantity.
        purchase.quantity -= self.quantity
        sale.quantity += self.quantity

    def append_to_container_positions(self, container):
        """Save a Daytrade object in the container positions.

        If there is already a daytrade with the same asset on the
        container's position, then the daytrades are merged.
        """
        if 'daytrades' not in container.positions:
            container.positions['daytrades'] = {}
        symbol = self.asset.symbol

        # If the container already have
        # a daytrade position with this asset,
        # then we must merge this daytrade
        # with the existing daytrade
        if symbol in container.positions['daytrades']:

            # Merges the purchase operation
            merge_operations(
                container.positions['daytrades'][symbol].operations[0],
                self.operations[0]
            )

            # Merges the sale operation
            merge_operations(
                container.positions['daytrades'][symbol].operations[1],
                self.operations[1]
            )

            # Update the daytraded quantity with the
            # quantity of this daytrade
            container.positions['daytrades'][symbol].quantity += self.quantity

        # If this is the first found daytrade
        # with this asset on the container, then
        # place this daytrade on the container
        else:
            container.positions['daytrades'][symbol] = self


def fetch_daytrades(container):
    """A OperationContainer task.

    Fetch the daytrades from the OperationContainer operations.

    The daytrades are placed on the container positions under the
    'daytrades' key, inexed by the Daytrade asset's symbol.
    """
    for i, operation_a in enumerate(container.operations):
        for operation_b in container.operations[i:]:
            if daytrade_condition(operation_a, operation_b):
                Daytrade(operation_a, operation_b)\
                    .append_to_container_positions(container)


def daytrade_condition(operation_a, operation_b):
    """Checks if the operations are day trades."""
    return (
        operation_a.asset.symbol == operation_b.asset.symbol and
        not same_sign(operation_a.quantity, operation_b.quantity) and
        operation_a.quantity != 0 and
        operation_b.quantity != 0
    )


def find_purchase_and_sale(operation_a, operation_b):
    """Find which is a purchase and which is a sale."""
    if same_sign(operation_a.quantity, operation_b.quantity):
        return None, None
    if operation_a.quantity > operation_b.quantity:
        return operation_a, operation_b
    return operation_b, operation_a
