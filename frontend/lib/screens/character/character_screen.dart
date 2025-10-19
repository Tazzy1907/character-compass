import 'package:flutter/material.dart';
import '../../api/api_service.dart';
import '../../models/character_details.dart';
import '../../style.dart';
import 'chat_screen.dart';

class CharacterScreen extends StatefulWidget {
  final int characterId;

  const CharacterScreen({super.key, required this.characterId});

  @override
  State<CharacterScreen> createState() => _CharacterScreenState();
}

class _CharacterScreenState extends State<CharacterScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  CharacterDetails? _character;
  String? _error;
  bool _isLoading = true;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _fetchCharacter();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchCharacter() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final character = await _apiService.fetchCharacterById(
        widget.characterId,
      );
      setState(() {
        _character = character;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _openChat() {
    if (_character == null) return;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ChatScreen(character: _character!),
      ),
    );
  }

  String _capitalize(String text) {
    if (text.isEmpty) return text;
    return text[0].toUpperCase() + text.substring(1);
  }

  bool _shouldShowChatButton() {
    if (_character == null) return false;

    // Don't show chat for side characters
    if (_character!.characterType.toLowerCase() == 'side') {
      return false;
    }

    // Don't show chat if character has no meaningful information
    bool hasAnyInfo =
        _character!.hasPersonality ||
        _character!.hasAppearance ||
        _character!.hasBackstory ||
        _character!.hasRelationships ||
        _character!.hasGoals ||
        _character!.hasMotivations ||
        _character!.age != null ||
        (_character!.occupation != null && _character!.occupation!.isNotEmpty);

    return hasAnyInfo;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F8),
      appBar: AppBar(
        backgroundColor: darkColor,
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.white),
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
      ),
      body: _buildBody(),
      floatingActionButton: _shouldShowChatButton()
          ? FloatingActionButton.extended(
              onPressed: _openChat,
              backgroundColor: highlightColor,
              icon: const Icon(Icons.chat_bubble, color: Colors.white),
              label: const Text("Chat", style: TextStyle(color: Colors.white)),
            )
          : null,
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                'Error loading character',
                style: TextStyle(fontSize: 18, color: Colors.grey[700]),
              ),
              const SizedBox(height: 8),
              Text(
                _error!,
                style: TextStyle(fontSize: 14, color: Colors.grey[500]),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _fetchCharacter,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: highlightColor,
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (_character == null) {
      return const Center(child: Text('No character data'));
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Card(
          elevation: 8,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: [
              // Tab Bar at the top of the card
              Container(
                decoration: BoxDecoration(
                  color: darkColor,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(16),
                    topRight: Radius.circular(16),
                  ),
                ),
                child: TabBar(
                  controller: _tabController,
                  indicatorColor: highlightColor,
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.white70,
                  indicatorWeight: 3,
                  tabs: const [
                    Tab(icon: Icon(Icons.person), text: "Overview"),
                    Tab(icon: Icon(Icons.history_edu), text: "Backstory"),
                    Tab(icon: Icon(Icons.people), text: "Relationships"),
                    Tab(icon: Icon(Icons.flag), text: "Goals"),
                  ],
                ),
              ),
              // Tab Content
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildOverviewTab(),
                    _buildBackstoryTab(),
                    _buildRelationshipsTab(),
                    _buildGoalsTab(),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Character Header
          Center(
            child: Column(
              children: [
                Stack(
                  children: [
                    CircleAvatar(
                      backgroundColor: highlightColor.withOpacity(0.2),
                      radius: 50,
                      child: Icon(Icons.person, size: 60, color: darkColor),
                    ),
                    if (_character!.characterType.toLowerCase() == 'main')
                      Positioned(
                        right: 0,
                        bottom: 0,
                        child: Container(
                          padding: const EdgeInsets.all(4.0),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.2),
                                blurRadius: 4.0,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: const Icon(
                            Icons.emoji_events,
                            size: 24.0,
                            color: Color(0xFFFFD700),
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  _character!.name,
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),

          // Basic Info Section
          _buildInfoSection('Basic Information', Icons.info_outline, [
            if (_character!.age != null)
              _buildInfoRow('Age', '${_character!.age}'),
            if (_character!.gender != null)
              _buildInfoRow('Gender', _capitalize(_character!.gender!)),
            if (_character!.sex != null)
              _buildInfoRow('Sex', _capitalize(_character!.sex!)),
            if (_character!.race != null)
              _buildInfoRow('Race', _capitalize(_character!.race!)),
            if (_character!.occupation != null &&
                _character!.occupation!.isNotEmpty)
              _buildInfoRow('Occupation', _capitalize(_character!.occupation!)),
          ]),

          // Personality Section
          if (_character!.hasPersonality) ...[
            const SizedBox(height: 24),
            _buildTextSection(
              'Personality',
              Icons.psychology,
              _character!.personality!,
            ),
          ],

          // Appearance Section
          if (_character!.hasAppearance) ...[
            const SizedBox(height: 24),
            _buildTextSection(
              'Appearance',
              Icons.face,
              _character!.appearance!,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBackstoryTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: _character!.hasBackstory
          ? _buildTextSection(
              'Backstory',
              Icons.history_edu,
              _character!.backstory!,
            )
          : Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.history_edu, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    'No backstory available',
                    style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildRelationshipsTab() {
    return _character!.hasRelationships
        ? ListView.builder(
            padding: const EdgeInsets.all(24),
            itemCount: _character!.relationships.length,
            itemBuilder: (context, index) {
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: lightColor.withOpacity(0.3),
                      child: Icon(Icons.person, color: darkColor),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        _character!.relationships[index],
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  ],
                ),
              );
            },
          )
        : Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.people_outline, size: 64, color: Colors.grey[400]),
                const SizedBox(height: 16),
                Text(
                  'No relationships recorded',
                  style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                ),
              ],
            ),
          );
  }

  Widget _buildGoalsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Goals Section
          _buildBulletSection(
            'Goals',
            Icons.flag,
            _character!.goals,
            highlightColor,
          ),
          const SizedBox(height: 32),
          // Motivations Section
          _buildBulletSection(
            'Motivations',
            Icons.psychology,
            _character!.motivations,
            lightColor,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoSection(String title, IconData icon, List<Widget> children) {
    if (children.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: darkColor, size: 24),
            const SizedBox(width: 12),
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: darkColor,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: children,
          ),
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }

  Widget _buildTextSection(String title, IconData icon, String content) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: darkColor, size: 24),
            const SizedBox(width: 12),
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: darkColor,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            content,
            style: const TextStyle(fontSize: 16, height: 1.6),
          ),
        ),
      ],
    );
  }

  Widget _buildBulletSection(
    String title,
    IconData icon,
    List<String> items,
    Color color,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(width: 12),
            Text(
              title,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (items.isEmpty)
                Text(
                  'No $title recorded',
                  style: TextStyle(
                    fontSize: 15,
                    color: Colors.grey[600],
                    fontStyle: FontStyle.italic,
                  ),
                )
              else
                ...items.asMap().entries.map((entry) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          margin: const EdgeInsets.only(top: 6),
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: color,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            entry.value,
                            style: const TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
            ],
          ),
        ),
      ],
    );
  }
}
