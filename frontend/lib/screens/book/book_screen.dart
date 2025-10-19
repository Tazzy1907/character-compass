import 'package:flutter/material.dart';
import '../../api/api_service.dart';
import '../../models/character_item.dart';
import '../../style.dart';
import '../character/character_screen.dart';

enum CharacterFilter { all, main, side }

class BookScreen extends StatefulWidget {
  final String bookId;
  const BookScreen({super.key, required this.bookId});

  @override
  State<BookScreen> createState() => _BookScreenState();
}

class _BookScreenState extends State<BookScreen> {
  final ApiService _apiService = ApiService();
  List<CharacterItem>? _items;
  String? _error;
  bool _isLoading = true;
  CharacterFilter _currentFilter = CharacterFilter.all;

  @override
  void initState() {
    super.initState();
    // Fetch the initial list of items when the widget is first created.
    _fetchItems();
  }

  Future<void> _fetchItems() async {
    try {
      final items = await _apiService.fetchCharacterItems(widget.bookId);
      setState(() {
        _items = items;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  List<CharacterItem> _getFilteredItems() {
    if (_items == null) return [];

    switch (_currentFilter) {
      case CharacterFilter.main:
        return _items!
            .where((item) => item.characterType.toLowerCase() == 'main')
            .toList();
      case CharacterFilter.side:
        return _items!
            .where((item) => item.characterType.toLowerCase() == 'side')
            .toList();
      case CharacterFilter.all:
        return _items!;
    }
  }

  Widget _buildFilterChips() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildFilterChip('All', CharacterFilter.all, null),
            const SizedBox(width: 8.0),
            _buildFilterChip(
              'Main Character',
              CharacterFilter.main,
              const Icon(
                Icons.emoji_events,
                size: 16.0,
                color: Color(0xFFFFD700),
              ),
            ),
            const SizedBox(width: 8.0),
            _buildFilterChip('Side Character', CharacterFilter.side, null),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, CharacterFilter filter, Widget? icon) {
    final isSelected = _currentFilter == filter;
    return FilterChip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[icon, const SizedBox(width: 4.0)],
          Text(label),
        ],
      ),
      selected: isSelected,
      onSelected: (selected) {
        setState(() {
          _currentFilter = filter;
        });
      },
      selectedColor: highlightColor.withOpacity(0.3),
      checkmarkColor: darkColor,
      labelStyle: TextStyle(
        color: isSelected ? darkColor : Colors.grey[700],
        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
      ),
    );
  }

  Widget _buildCharacterAvatar(CharacterItem item) {
    final isMainCharacter = item.characterType.toLowerCase() == 'main';

    return Stack(
      children: [
        CircleAvatar(
          radius: 28.0,
          backgroundColor: highlightColor.withOpacity(0.2),
          child: Icon(Icons.person, size: 32.0, color: darkColor),
        ),
        if (isMainCharacter)
          Positioned(
            right: 0,
            bottom: 0,
            child: Container(
              padding: const EdgeInsets.all(2.0),
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 3.0,
                    offset: const Offset(0, 1),
                  ),
                ],
              ),
              child: const Icon(
                Icons.emoji_events,
                size: 18.0,
                color: Color(0xFFFFD700), // Gold color for crown
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildCharacterList(List<CharacterItem> items) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12.0),
          elevation: 2.0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.0),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            leading: _buildCharacterAvatar(item),
            title: Text(
              item.name,
              style: const TextStyle(
                fontSize: 16.0,
                fontWeight: FontWeight.w600,
              ),
            ),
            trailing: Icon(Icons.chevron_right, color: Colors.grey[400]),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => CharacterScreen(characterId: item.id),
                ),
              );
            },
          ),
        );
      },
    );
  }

  // Helper method to decide which widget to show based on the current state.
  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(child: Text('Error: $_error'));
    }
    if (_items == null || _items!.isEmpty) {
      return const Center(child: Text('No characters found.'));
    }

    final filteredItems = _getFilteredItems();

    return Column(
      children: [
        _buildFilterChips(),
        Expanded(
          child: filteredItems.isEmpty
              ? const Center(
                  child: Text('No characters match the selected filter.'),
                )
              : _buildCharacterList(filteredItems),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: darkColor,
        centerTitle: true,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'icons/Character Compass Icon.jpeg',
              height: 32,
              fit: BoxFit.contain,
            ),
            const SizedBox(width: 12),
            const Text(
              "CharacterCompass",
              style: TextStyle(color: Colors.white),
            ),
          ],
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: _buildBody(),
    );
  }
}
