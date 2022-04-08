import sys
import argparse

"""
Author: William Noonan
        CSCI 5362 Operating Systems
        Contiguous Memory Allocation Assignment
        31 Mar 2022

        Python implementation of the continuous memory allocation program. Note that when holes are compacted, I
        assumed that the combined hole should go to the end of the list of memory blocks.

        To run the allocator prompt:
            python ContiguousMemoryAllocation.py <MAX>
            
        where 
            MAX is the maximum available memory
        
"""


class Block:
    """
    Represents a memory block, either free or allocated
    """
    def __init__(self, start_address: int, end_address: int, ID: str):
        self.start = start_address
        self.end = end_address
        self.id = ID
        self._size = end_address - start_address + 1

    @property
    def size(self):
        # the size of each block should remain constant, so I protected it
        # otherwise a new Block instance should be made
        return self._size

    def __repr__(self):
        """String representation of an instance"""
        return f"[{self.start}:{self.end}] {self.id}"


class Memory:
    """
    Represents list of contiguous computer memory blocks.
    """
    def __init__(self, MAX_MEMORY=10000):
        self.memory = [Block(0, MAX_MEMORY - 1, "unused")]
        self.unique_ids = set()

    def _sort_by_starting_address_increasing(self):
        """
        Helper function to sort the memory blocks from smallest to largest starting address.
        :return: None
        """
        self.memory.sort(key=lambda block: block.start, reverse=False)

    def _check_process_already_allocated(self, process: str):
        if process in self.unique_ids:
            print(f"Error: Memory already allocated for '{process}'")
            return True
        return False

    def _get_free_blocks_for_size_with_index(self, size: int):
        free_blocks = [(index, item) for index, item in enumerate(self.memory) if item.id == "unused" and size <= item.size]
        return free_blocks


    def addMemoryFirstFit(self, process: str, size: int):
        """
        Allocates memory to the first hole (free block) that is big enough.
        :param process:
        :param size:
        :return:
        """
        if self._check_process_already_allocated(process):
            return

        free_indices = [index for index, item in enumerate(self.memory) if item.id == "unused" and size <= item.size]
        if not free_indices:
            print("Error: Insufficient memory, cannot allocate.")
            return

        first_free = self.memory.pop(free_indices[0])  # remove first free block from memory to replace it
        new_block = Block(first_free.start, first_free.start + size - 1, process)
        new_blocks = [new_block]
        if size < first_free.size:
            new_blocks.append(Block(new_block.end + 1, first_free.end, "unused"))

        self.unique_ids.add(process)
        self.memory.extend(new_blocks)
        self._sort_by_starting_address_increasing()

    def addMemoryBestFit(self, process: str, size: int):
        """
        Allocates the smallest free block that is large enough.
        :param process: ID of process
        :param size: size of contiguous memory to allocate
        :return: None
        """
        # check if process is already in memory
        if self._check_process_already_allocated(process):
            return

        # get list of free blocks and hold onto their index in the list of memory
        free_blocks = self._get_free_blocks_for_size_with_index(size)
        # the list of free will be empty if there's no room left
        if not free_blocks:
            print("Error: Insufficient memory, cannot allocate.")
            return

        # make sure the free blocks are sorted from smallest to largest size
        free_blocks.sort(key=lambda tup: tup[1].size, reverse=False)
        # the first hole in the list is the best one
        best_index, best_hole = free_blocks[0]

        # remove the hole from memory
        self.memory.pop(best_index)

        # create a new block of free memory using the best hole's starting address and the process's size
        new_block = Block(best_hole.start, best_hole.start + size - 1, process)
        # start a list with it
        new_blocks = [new_block]
        # if there is room in the hole leftover:
        if size < best_hole.size:
            # create a new block of free memory
            new_blocks.append(Block(new_block.end + 1, best_hole.end, "unused"))

        # add the process to the set of unique processes in memory
        self.unique_ids.add(process)
        # add the new memory blocks to memory
        self.memory.extend(new_blocks)
        # sort memory from smallest to largest lower bound
        self._sort_by_starting_address_increasing()

    def addMemoryWorstFit(self, process: str, size: int):
        # if the process has already been allocated memory
        if self._check_process_already_allocated(process):
            return

        # get list of free blocks in memory
        free_blocks = self._get_free_blocks_for_size_with_index(size)
        # if the list is empty there's no room
        if not free_blocks:
            print("Error: Insufficient memory, cannot allocate.")
            return

        # sort free blocks from largest to smallest
        free_blocks.sort(key=lambda tup: tup[1].size, reverse=True)
        # the first free block in the list has the largest size
        worst_index, worst_hole = free_blocks[0]

        # remove the block from memory
        self.memory.pop(worst_index)

        # create a new block of free memory using the worst hole's starting address and the process's size
        new_block = Block(worst_hole.start, worst_hole.start + size - 1, process)
        # start a new list with it
        new_blocks = [new_block]
        # if there is room in the hole leftover:
        if size < worst_hole.size:
            new_blocks.append(Block(new_block.end + 1, worst_hole.end, "unused"))

        # add the process to the set of unique processes in memory
        self.unique_ids.add(process)
        # add the new memory blocks to memory
        self.memory.extend(new_blocks)
        # sort memory from smallest to largest starting address
        self._sort_by_starting_address_increasing()

    def release(self, process: str) -> None:
        """
        Release memory allocated to a process.
        :param process: string ID of process
        :return: None
        """
        # if the process is not in the set of unique IDs, it doesn't exist in memory
        if process not in self.unique_ids:
            print(f"Error: '{process}' does not exist in memory")
            return

        # find the index in memory where the target process is
        index = 0
        for i, item in enumerate(self.memory):
            if item.id == process:
                index = i
                break

        # just set the ID of the Block instance for the process to "unused"
        self.memory[index].id = "unused"
        # remove the process from the set of unique processes
        self.unique_ids.remove(process)
        # combine any adjacent holes that resulted from the process removal
        self._combine_adjacent_holes()

    def _combine_adjacent_holes(self) -> None:
        """
        Helper function called by release to combine adjacent free blocks (holes), which only appear after a release
        occurs. Not meant to be directly invoked by the user.
        :return: None
        """
        # get list of free blocks in memory, must hold onto index to know what to merge
        free_blocks = [(index, item) for index, item in enumerate(self.memory) if item.id == "unused"]
        to_merge = []  # list to hold adjacent free blocks to merge
        new_blocks = []  # list to hold merged free blocks
        i = 0
        while i < len(free_blocks):
            block = free_blocks[i]  # tuple of (index, block)
            # if to_merge is empty or the last block in to_merge has an index 1 less than current block:
            if not to_merge or to_merge[-1][0] == (block[0] - 1):
                to_merge.append(block)  # append the block
            else:
                # otherwise the run has ended, append a new Block instance new_blocks using the first and last free
                # in to_merge
                new_blocks.append(Block(to_merge[0][1].start, to_merge[-1][1].end, "unused"))
                # emtpy the to_merge list
                to_merge = []
                # continue the loop without moving to the next block in free
                continue
            i += 1

        # if there are blocks remaining in to_merge, append a new Block to new_blocks just like before
        if to_merge:
            new_blocks.append(Block(to_merge[0][1].start, to_merge[-1][1].end, "unused"))

        # get the blocks from memory that are allocated, the free blocks will be ignored
        new_memory = [item for item in self.memory if item.id != "unused"]
        # add the list of new free blocks to the list of allocated memory blocks
        new_memory.extend(new_blocks)
        # update the memory list
        self.memory = new_memory
        # sort it from smallest to largest lower bound
        self._sort_by_starting_address_increasing()

    def compactAllHoles(self) -> None:
        """
        Compacts (combines) all free blocks that exist anywhere in memory. Assumes that the combined hole should go
        to the end of the list of memory blocks.

        :return: None
        """
        # get list of free blocks in memory, there is no need to hold onto its index
        free_blocks = [item for item in self.memory if item.id == "unused"]
        # if there are less than 2, there's nothing to compact
        if len(free_blocks) < 2:
            # print("Warning: No free blocks to compact")
            return

        # get the list of allocated memory blocks
        allocated_memory = [item for item in self.memory if item.id != "unused"]

        # shift all allocated memory blocks to the front starting at address 0 by making a new list, this
        # must be done before combining the free blocks in order to know at what address to start the combined block
        start_address = 0  # starting address
        new_memory = []  # list to hold new memory blocks both used and unused
        for am in allocated_memory:
            # append a new Block instance using starting address and current block's size and ID
            new_memory.append(Block(start_address, start_address + am.size - 1, am.id))
            start_address += am.size

        # append a new Block instance that represents the combined free blocks
        new_memory.append(Block(start_address, start_address + sum(item.size for item in free_blocks) - 1, "unused"))

        # update list of memory, no need to sort because it already is
        self.memory = new_memory

    def printStat(self):
        """
        Prints the memory addresses of both free and allocated memory blocks.
        :return:
        """
        for item in self.memory:
            address_str = f"Addresses [{item.start}:{item.end}] "
            id_str = "Unused" if item.id == "unused" else f"Process {item.id}"
            print(address_str + id_str)

    def __repr__(self):
        """Represents the Memory instance as a string of the list of memory blocks."""
        return str(self.memory)



def testing():
    """
    Standalone function for testing.
    :return:
    """
    mem = Memory(10000)
    mem.addMemoryFirstFit("P1", 500)
    mem.addMemoryFirstFit("P2", 400)
    mem.addMemoryFirstFit("P3", 300)
    mem.addMemoryFirstFit("P4", 200)
    mem.addMemoryFirstFit("P5", 100)
    mem.release("P2")
    mem.release("P4")
    mem.addMemoryBestFit("p9", 50)
    mem.release("p9")
    mem.printStat()


def main():
    """
    Main function that runs the allocator prompt. Must be run from the command line.

    Usage:
        python ContiguousMemoryAllocation.py <MAX>

    :return:
    """
    # Parse initial command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("MAX", type=int)
    args = parser.parse_args()

    # create instance of Memory using user-defined MAX value
    mem = Memory(args.MAX)

    # loop
    while True:
        # get user input
        user_args = input("allocator>")
        # clean the raw input
        user_args = [arg.strip() for arg in user_args.split(" ") if arg]

        if not user_args:
            continue

        # Parse the user args
        first_arg = user_args[0]  # first user arg
        if first_arg == "X":
            # user wants to quit
            sys.exit()
        elif first_arg == "STAT":
            # user wants to print stat info
            mem.printStat()
        elif first_arg == "C":
            # user wants to compact all holes that exist anywhere in memory
            mem.compactAllHoles()
        elif first_arg == "RL" and len(user_args) == 2:
            # user wants to release a process
            mem.release(user_args[1])
        elif first_arg == "RQ" and len(user_args) == 4:
            # user wants to allocate memory to a new process
            process, size, approach = user_args[1:]
            size = int(size)
            if approach == "F":
                # user wants First-fit allocation
                mem.addMemoryFirstFit(process, size)
            elif approach == "B":
                # user wants Best-fit allocation
                mem.addMemoryBestFit(process, size)
            elif approach == "W":
                # user wants Worst-fit allocation
                mem.addMemoryWorstFit(process, size)
            else:
                # user supplied a bad arg or incomplete args
                print("command not recognized")
        else:
            # user supplied an unrecognized arg
            print("command not recognized")


if __name__ == "__main__":
    main()
