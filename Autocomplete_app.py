import pygame
import sys
from collections import deque

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT, FPS, NODE_RADIUS = 1000, 600, 60, 18

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (66, 133, 244)
LIGHT_BLUE = (200, 220, 255)
GREEN = (52, 168, 83)
HIGHLIGHT_COLOR = (255, 235, 59)
EDGE_COLOR = (180, 180, 180)
                                                                        
FONT_SMALL = pygame.font.Font(None, 20)
FONT_MEDIUM = pygame.font.Font(None, 26)
FONT_INPUT = pygame.font.Font(None, 36)

class TrieNode:
    def __init__(self, char=''):
        self.char = char
        self.children = {}
        self.is_end_of_word = False
        self.word = None  
        self.x, self.y = 0, 0
        self.is_path_node = False 
        self.is_in_subtree = False

class Trie:
    def __init__(self):
        self.root = TrieNode('*')
    
    def insert(self, word):
        if not word: return
        word = word.lower()
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode(char)
            node = node.children[char]
        node.is_end_of_word = True
        node.word = word
    
    def get_suggestions(self, prefix):
        if not prefix: return [], None
        prefix = prefix.lower()
        node = self.root
        for char in prefix:
            if char not in node.children: return [], None
            node = node.children[char]
        
        suggestions = []
        self._collect_all_words(node, suggestions)
        suggestions.sort(key=lambda x: (len(x), x))
        return suggestions, node
    
    def _collect_all_words(self, node, words, max_words=8): 
        if len(words) >= max_words: return
        if node.is_end_of_word: words.append(node.word)
        for char in sorted(node.children.keys()):
            self._collect_all_words(node.children[char], words, max_words)
    
    def highlight_path(self, prefix):
        self._reset_highlights(self.root)
        if not prefix: return
        
        prefix = prefix.lower()
        node = self.root
        for char in prefix:
            if char not in node.children: return
            node = node.children[char]
            node.is_path_node = True
        self._mark_suggestion_subtree(node)
    
    def _reset_highlights(self, node):
        node.is_path_node = False
        node.is_in_subtree = False
        for child in node.children.values():
            self._reset_highlights(child)
    
    def _mark_suggestion_subtree(self, node):
        node.is_in_subtree = True
        for child in node.children.values():
            self._mark_suggestion_subtree(child)
    
    def get_all_nodes(self):
        nodes = []
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            nodes.append(node)
            for child in node.children.values():
                queue.append(child)
        return nodes

class TextBox:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.cursor_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.key == pygame.K_RETURN: return False
            elif len(self.text) < 25:
                if event.unicode.isalpha() or event.unicode.isspace():
                    self.text += event.unicode
                    return True
        return False
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30: self.cursor_timer = 0
    
    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLUE, self.rect, 2, border_radius=8)
        text_surface = FONT_INPUT.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.x + 15, self.rect.y + 12))
        
        if self.cursor_timer < 15:
            cursor_x = self.rect.x + 15 + text_surface.get_width() + 2
            pygame.draw.line(screen, BLACK, (cursor_x, self.rect.y + 10), 
                             (cursor_x, self.rect.y + 35), 2)
    
    def get_text(self): return self.text.strip()
    def set_text(self, text): self.text = text

class TrieVisualizer:
    def __init__(self):
        self.level_height = 65
        self.horizontal_spacing = 40
        self.start_y = 100
        self.draw_area_width = SCREEN_WIDTH 

    def calculate_node_positions(self, trie):
        if not trie.root: return

        leaf_counts = {}
        def get_leaf_count(node):
            if not node.children:
                leaf_counts[node] = 1
                return 1
            count = sum(get_leaf_count(child) for child in node.children.values())
            leaf_counts[node] = count
            return count

        root_leaves = get_leaf_count(trie.root)
        total_tree_width = root_leaves * self.horizontal_spacing
        start_x = (self.draw_area_width - total_tree_width) // 2
        if start_x < 20: start_x = 20

        def position_node(node, x, y):
            node_width = leaf_counts[node] * self.horizontal_spacing
            node.x = x + node_width // 2
            node.y = y
            
            current_x = x
            sorted_children = sorted(node.children.values(), key=lambda n: n.char)
            for child in sorted_children:
                child_pixel_width = leaf_counts[child] * self.horizontal_spacing
                position_node(child, current_x, y + self.level_height)
                current_x += child_pixel_width

        position_node(trie.root, start_x, self.start_y)

    def draw_structure(self, screen, trie):
        if not trie.root.children:
            trie.root.x = SCREEN_WIDTH // 2
            trie.root.y = self.start_y
            self._draw_node(screen, trie.root)
            return

        self._draw_edges(screen, trie.root)
        for node in trie.get_all_nodes():
            self._draw_node(screen, node)

    def _draw_edges(self, screen, node):
        for child in node.children.values():
            if child.is_path_node:
                color, width = BLUE, 3
            elif child.is_in_subtree:
                color, width = GREEN, 2
            else:
                color, width = EDGE_COLOR, 1
            
            pygame.draw.line(screen, color, (node.x, node.y), (child.x, child.y), width)
            self._draw_edges(screen, child)

    def _draw_node(self, screen, node):
        if node.is_path_node:
            color, border_color, border_width = HIGHLIGHT_COLOR, BLUE, 3
        elif node.is_in_subtree:
            color, border_color, border_width = (220, 255, 220), GREEN, 2
        else:
            color, border_color, border_width = WHITE, BLACK, 1
        
        pygame.draw.circle(screen, color, (node.x, node.y), NODE_RADIUS)
        pygame.draw.circle(screen, border_color, (node.x, node.y), NODE_RADIUS, border_width)
        
        if node.is_end_of_word:
            pygame.draw.circle(screen, border_color, (node.x, node.y), NODE_RADIUS - 4, 1)
        
        char_text = node.char.upper()
        font = FONT_MEDIUM if node.char == 'R' else FONT_SMALL
        text_surface = font.render(char_text, True, BLACK)
        text_rect = text_surface.get_rect(center=(node.x, node.y))
        screen.blit(text_surface, text_rect)

class AutocompleteApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Trie Autocomplete Visualizer")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.trie = Trie()
        self.visualizer = TrieVisualizer()
        self.textbox = TextBox(20, 20, 400, 50)
        
        self.current_suggestions = []
        self.load_initial_words()
        self.visualizer.calculate_node_positions(self.trie)
        
        self.suggestion_rect = None

    def load_initial_words(self):
        words = ["algo", "aufa", "alga", "apple", "batik", "batu", "bata", "baca", 
                 "cara", "cari", "cuma", "cat", "car", "code", "coder", 
                 "data", "date", "diskrit", "fathan", "hedo", "zahy", "zara", "zebra"]
        for word in words: self.trie.insert(word)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            
            if self.textbox.handle_event(event):
                self.update_autocomplete()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.suggestion_rect:
                mouse_x, mouse_y = event.pos
                if self.suggestion_rect.collidepoint(mouse_x, mouse_y):
                    relative_y = mouse_y - self.suggestion_rect.top
                    index = int(relative_y / 30)
                    if 0 <= index < len(self.current_suggestions):
                        self.textbox.set_text(self.current_suggestions[index])
                        self.update_autocomplete()
    
    def update_autocomplete(self):
        prefix = self.textbox.get_text()
        suggestions, _ = self.trie.get_suggestions(prefix) 
        self.current_suggestions = suggestions
        self.trie.highlight_path(prefix)
    
    def draw_suggestions(self):
        if not self.current_suggestions:
            self.suggestion_rect = None
            return

        x, y = self.textbox.rect.x, self.textbox.rect.bottom + 5
        width = self.textbox.rect.width
        item_height = 30
        height = len(self.current_suggestions) * item_height

        self.suggestion_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, WHITE, self.suggestion_rect, border_radius=5)
        pygame.draw.rect(self.screen, GRAY, self.suggestion_rect, 1, border_radius=5)

        for i, word in enumerate(self.current_suggestions):
            item_y = y + i * item_height
            item_rect = pygame.Rect(x + 1, item_y, width - 2, item_height)
            
            prefix = self.textbox.get_text()
            if prefix:
                prefix_text = word[:len(prefix)]
                rest_text = word[len(prefix):]
                
                prefix_surface = FONT_MEDIUM.render(prefix_text, True, BLUE)
                self.screen.blit(prefix_surface, (item_rect.x + 10, item_rect.y + 5))
                
                rest_surface = FONT_MEDIUM.render(rest_text, True, BLACK)
                self.screen.blit(rest_surface, 
                                 (item_rect.x + 10 + prefix_surface.get_width(), item_rect.y + 5))
            else:
                word_surface = FONT_MEDIUM.render(word, True, BLACK)
                self.screen.blit(word_surface, (item_rect.x + 10, item_rect.y + 5))

    def draw_ui_info_and_keterangan(self):
        start_x = 430 
        start_y = 15
        line_height = 18
        
        font_info = pygame.font.Font(None, 22)

        prefix = self.textbox.get_text()
        total_words = sum(1 for node in self.trie.get_all_nodes() if node.is_end_of_word)
        
        disp_prefix = (prefix[:10] + '..') if len(prefix) > 10 else prefix

        info_list = [
            f"Total Kata: {total_words}",
            f"Prefix: '{disp_prefix}'",
            f"Ditemukan: {len(self.current_suggestions)}"
        ]
        
        for i, text in enumerate(info_list):
            color = GREEN if "Ditemukan" in text and len(self.current_suggestions) > 0 else BLACK
            info_surface = font_info.render(text, True, color)
            self.screen.blit(info_surface, (start_x, start_y + (i * line_height)))

        keterangan_start_x = start_x + 120
        
        keterangan = [
            (HIGHLIGHT_COLOR, BLUE, "Lintasan Prefix", 3),
            ((220, 255, 220), GREEN, "Saran Kata", 2),
            (WHITE, BLACK, "Akhir Kata", 2),
        ]
        
        for i, (color, border, label, width) in enumerate(keterangan):
            row_y = start_y + (i * line_height)

            circle_center = (keterangan_start_x, row_y + 7)
            pygame.draw.circle(self.screen, color, circle_center, 6)
            pygame.draw.circle(self.screen, border, circle_center, 6, width)

            if label == "Akhir Kata":
                 pygame.draw.circle(self.screen, border, circle_center, 2)

            label_surface = font_info.render(label, True, BLACK)
            self.screen.blit(label_surface, (keterangan_start_x + 15, row_y))
    
    def draw(self):
        self.screen.fill(WHITE)
        
        self.textbox.draw(self.screen)
        self.draw_suggestions()

        self.visualizer.draw_structure(self.screen, self.trie) 
        
        self.draw_ui_info_and_keterangan()     

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.textbox.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = AutocompleteApp() 
    app.run()

    