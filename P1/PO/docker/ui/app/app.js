// app.js

const { useState,useEffect } = React;
//todo meter esto en una variable de entorno (Nombre del servicio, y el puerto)
const API_URL = 'http://localhost:5005';

function App() {
  // Estado para controlar la pantalla actual
  const [screen, setScreen] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Validar campos en blanco
  const validateFields = () => {
    if (username === '' || password === '') {
      setErrorMessage('Please fill in all fields.');
      return false;
    }
    setErrorMessage('');
    return true;
  };

  const handleScreenChange = (newScreen) => {
    setScreen(newScreen);
  };

  // Manejar login
  const handleLogin = async () => {
    if (!validateFields()) return;
  
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });
  
    const result = await response.json();
    if (result.status === 'Inicio de sesión exitoso') {
      // Guardar el username en localStorage
      localStorage.setItem('username', username);
      handleScreenChange('ask'); // Cambiar pantalla después de login exitoso
    } else {
      alert("Wrong credentials")
      setErrorMessage('Invalid login credentials.');
    }
  };
  
  

  // Manejar registro
  const handleRegister = async () => {
    if (!validateFields()) return;

    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (result.status === 'Usuario registrado con éxito') {
      alert('User registered successfully!');
    } else {
      setErrorMessage('Registration failed.');
    }
  };

  const handleLogout = () => {
    setUsername('');
    setPassword('');
    handleScreenChange('login');
  };
  const handleAsk = async () => {
    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: updatedPrompt })
      });

      const result = await response.json();
      if (response.status === 200) {
        setAskResults(result);
      } else {
        setAskError(result.error || 'Error during ask request.');
      }
    } catch (error) {
      setAskError('Error occurred while making the ask request.');
    }
  };

  const handleUpdatePrompt = async () => {
    try {
      const response = await fetch(`${API_URL}/updatePrompt/${selectedPromptId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: updatedPrompt })
      });

      const result = await response.json();
      if (result.status === 'Prompt updated successfully') {
        alert('Prompt updated!');
        setPrompts(prompts.map(prompt => prompt.id === selectedPromptId ? { ...prompt, prompt: updatedPrompt } : prompt));
        setShowSubMenu(false); // Cerrar el submenú después de actualizar
      } else {
        alert('Failed to update prompt.');
      }
    } catch (error) {
      console.error('Error updating prompt:', error);
    }
  };

  const closeSubMenu = () => {
    setShowSubMenu(false);
    setAskResults([]);
    setAskError(null);
  };
  return (
    <div className="container">
      <h1 className="title">Song Prompt App</h1>
      {screen === 'login' ? (
        // Pantalla de inicio de sesión/registro
        <div className="section">
          <h2>Login or Register</h2>
          <input
            type="text"
            placeholder="Enter your username..."
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Enter your password..."
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="button" onClick={handleLogin}>
            Login
          </button>
          <button className="button" onClick={handleRegister}>
            Register
          </button>
        </div>
      ) : (
        // Pantalla principal de la aplicación
        <div>
          {/* Barra de navegación */}
          <nav className="nav">
            <button className="button" onClick={() => handleScreenChange('ask')}>Ask</button>
            <button className="button" onClick={() => handleScreenChange('search')}>Search Prompts</button>
            <button className="button" onClick={() => handleScreenChange('findFriends')}>Find Friends</button>
            <button className="button" onClick={() => handleScreenChange('Friends')}>Friends</button>
            <button className="button" onClick={() => handleScreenChange('feed')}>Feed</button>
            <button className="button" onClick={() => handleScreenChange('me')}>Me</button>
          </nav>
          {/* Contenido de la pantalla seleccionada */}
          <div className="content">
            {screen === 'ask' && <Ask />}
            {screen === 'search' && <SearchPrompts />}
            {screen === 'findFriends' && <FindFriends />}
            {screen === 'Friends' && <Friends />}
            {screen === 'feed' && <Feed />}
            {screen === 'me' && <Me onLogout={handleLogout} />}
          </div>
        </div>
      )}
    </div>
  );
}

// Componentes individuales para cada sección de la UI
// TODO CAMBIAR EL LOCAL HOST POR LAS VARIABLES DEL NODEPORT DE LA API

function Ask() {
  const [prompt, setPrompt] = useState('');
  const [results, setResults] = useState([]);

  const handleAsk = async () => {
    // Enviar el prompt a la ruta /ask de tu API Flask para realizar la búsqueda
    const response = await fetch(API_URL+'/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: prompt,  // Enviar el prompt como 'question' en JSON
      }),
    });

    // Parsear la respuesta JSON
    const result = await response.json();
    
    // Asignar los resultados a tu estado de resultados
    setResults(result);
  };

  const handleSubmitPrompt = async () => {
    const username = localStorage.getItem('username');
    const response = await fetch(API_URL+'/publish', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',  // Cambiar a application/json
      },
      body: JSON.stringify({
        username: username,
        prompt: prompt,
      }),
    });
  
    const result = await response.json();
    if (result.status === "Prompt publicado con éxito") {
      alert("¡Prompt publicado con éxito!");
    }
  };

  return (
    <div className="section">
      <h2>Ask a Song Prompt</h2>
      <input
        type="text"
        placeholder="Type your question here..."
        className="input"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      
      {/* Botón Ask */}
      <button className="button" onClick={handleAsk}>Ask</button>
      
      {/* Botón Submit para publicar el prompt */}
      <button className="button" onClick={handleSubmitPrompt}>Submit</button>

      {/* Mostrar los resultados de la búsqueda */}
      <div className="results">
        {results.length > 0 ? (
          results.map((result, index) => (
            <div key={index} className="result-item">
              <p><strong>Canción:</strong> {result.name || "Unknown Song"}</p>
              <p><strong>Artistas:</strong> {result.artists || "Unknown Artist"}</p>
              <p><strong>Letras:</strong> {result.lyrics || "No lyrics available"}</p>
              <hr />
            </div>
          ))
        ) : (
          <p>No results found</p>
        )}
      </div>
    </div>
  );
}

function SearchPrompts() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const response = await fetch(API_URL + `/search?keyword=${encodeURIComponent(searchTerm)}`);
    const result = await response.json();

    if (result.results) {
      setResults(result.results);
    } else {
      setResults([]);
    }
  };

  const handleLike = async (promptId, index) => {
    const username = localStorage.getItem('username');  // Obtener el username del usuario logueado
    
    const response = await fetch(API_URL + '/like', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',  // Cambiar el tipo de contenido a JSON
      },
      body: JSON.stringify({
        username: username,  // Enviar el username en lugar de user_id
        prompt_id: promptId,  // ID del prompt que fue liked
      }),
    });

    const result = await response.json();
    
    if (result.status === 'Prompt liked successfully') {
      alert('Prompt liked!');
      
      // Actualizar el contador de likes en el frontend (si la API también incrementa los likes)
      const updatedResults = [...results];
      updatedResults[index].likes += 1;  // Incrementar el número de likes localmente
      setResults(updatedResults);
    } else {
      alert('You have already liked this post');
    }
  };

  return (
    <div className="section">
      <h2>Search Prompts</h2>
      <input
        type="text"
        placeholder="Search..."
        className="input"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button className="button" onClick={handleSearch}>Search</button>

      <div className="results">
        {results.length > 0 ? (
          results.map((res, index) => (
            <div key={index} className="result-item">
              <p><strong>Prompt ID:</strong> {res.id}</p>
              <p><strong>Username:</strong> {res.username}</p>
              <p><strong>Prompt:</strong> {res.prompt}</p>
              <p><strong>Date:</strong> {res.date}</p>
              <p><strong>Likes:</strong> {res.likes}</p>  {/* Mostrar los likes */}
              <button className="button" onClick={() => handleLike(res.id, index)}>Like</button>
              <hr />
            </div>
          ))
        ) : (
          <p>No prompts found</p>
        )}
      </div>
    </div>
  );
}
function SearchPrompts() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [askResults, setAskResults] = useState([]);  // Para almacenar los resultados de Ask
  const [selectedPrompt, setSelectedPrompt] = useState(null);  // Para manejar el prompt seleccionado
  const [askError, setAskError] = useState(null); 
  const handleSearch = async () => {
    const response = await fetch(API_URL + `/search?keyword=${encodeURIComponent(searchTerm)}`);
    const result = await response.json();

    if (result.results) {
      setResults(result.results);
    } else {
      setResults([]);
    }
  };

  const handleLike = async (promptId, index) => {
    const username = localStorage.getItem('username');
    
    // Verificar que ambos datos estén presentes
    if (!username || !promptId) {
      console.error('Username or promptId is missing:', { username, promptId });
      alert('Error: Missing data.');
      return;
    }
  
    try {
      const response = await fetch(`${API_URL}/like`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          prompt_id: promptId,
        }),
      });
  
      // Verificar si la respuesta fue exitosa
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error from API:', errorData);
        throw new Error('Error from the API');
      }
  
      const result = await response.json();
      console.log(result); // Verificar qué devuelve el backend
  
      if (result.status === "Prompt liked and republished successfully") {
        alert('Prompt liked!');
  
        // Actualizar el número de likes con el valor devuelto por la API
        const updatedResults = results.map((prompt, i) => 
          i === index ? { ...prompt, likes: result.updated_likes } : prompt
        );
  
        // Actualizar el estado con el nuevo array de resultados
        setResults(updatedResults);
      } else {
        alert(result.error || 'Error liking prompt');
      }
    } catch (error) {
      console.error('Error in the like process:', error);  // Mostramos el error en la consola
      alert('An error occurred while liking the prompt.');
    }
  };
  

  const handleAsk = async (prompt) => {
    setSelectedPrompt(prompt);  // Guardar el prompt seleccionado
    setAskError(null);  // Limpiar errores previos
    setAskResults([]);  // Limpiar los resultados anteriores

    try {
      const response = await fetch(API_URL + '/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: prompt.prompt,  // Enviar la pregunta del prompt al backend
        }),
      });

      const result = await response.json();

      if (response.status === 200) {
        setAskResults(result);  // Almacenar los resultados de la búsqueda
      } else {
        setAskError(result.error || 'Error during ask request.');
      }
    } catch (error) {
      setAskError('Error occurred while making the ask request.');
    }
  };

  const closeModal = () => {
    setSelectedPrompt(null);
    setAskResults([]);
    setAskError(null);
  };

  return (
    <div className="section">
      <h2>Search Prompts</h2>
      <input
        type="text"
        placeholder="Search..."
        className="input"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button className="button" onClick={handleSearch}>Search</button>

      <div className="results">
        {results.length > 0 ? (
          results.map((res, index) => (
            <div key={index} className="result-item">
              <p><strong>Prompt ID:</strong> {res.id}</p>
              <p><strong>Username:</strong> {res.username}</p>
              <p><strong>Prompt:</strong> {res.prompt}</p>
              <p><strong>Date:</strong> {res.date}</p>
              <p><strong>Likes:</strong> {res.likes}</p>
              <button className="button" onClick={() => handleLike(res.id, index)}>Like</button>
              <button className="button ask-button" onClick={() => handleAsk(res)}>Ask</button> {/* Botón para hacer Ask */}
              <hr />
            </div>
          ))
        ) : (
          <p>No prompts found</p>
        )}
      </div>

      {/* Modal para mostrar los resultados del Ask */}
      {selectedPrompt && (
      <div className="modal-overlay">
        <div className="modal">
          <h3>Results for: {selectedPrompt.prompt}</h3>
          {askError ? (
            <p style={{ color: 'red' }}>{askError}</p>
          ) : (
            <div className="ask-results">
              {askResults.length > 0 ? (
                askResults.map((result, index) => (
                  <div key={index} className="ask-result-item card">
                    <h4 className="card-title">{result.name}</h4> {/* Estilo de título para la canción */}
                    <p><strong>Artists:</strong> {result.artists}</p>
                    <p><strong>Lyrics:</strong> {result.lyrics}</p>
                  </div>
                ))
              ) : (
                <p>No results found for this prompt.</p>
              )}
            </div>
          )}
          <button className="button close-button" onClick={closeModal}>Close</button>
        </div>
      </div>
    )}
    </div>
  );
}


function PromptItem({ promptId, promptText }) {
  const handleLike = async () => {
    const username = localStorage.getItem('username');  // Obtener el username del usuario logueado
    const response = await fetch(API_URL + '/like', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,  // Enviar el username
        prompt_id: promptId,  // Enviar el ID del prompt
      }),
    });
    const result = await response.json();
    if (result.error) {
      alert(result.error);  // Mostrar error si el usuario ya ha dado "like"
    } else {
      alert("Prompt liked successfully!");
    }
  };

  return (
    <div>
      <p>{promptText}</p>
      <button onClick={handleLike}>Like</button>
    </div>
  );
}



function FindFriends() {
  const [users, setUsers] = useState([]);
  const [searchId, setSearchId] = useState('');
  const [foundUser, setFoundUser] = useState(null);
  const [messageVisible, setMessageVisible] = useState(false);
  const username = localStorage.getItem('username');

  // Fetch random users when the component loads
  useEffect(() => {
    fetch(API_URL + '/friends/random')
      .then(response => response.json())
      .then(data => {
        if (data.users.length === 0) {
          setMessageVisible(true);  // Show hidden message if no users
        } else {
          setUsers(data.users);  // Store users (array of strings) in state
        }
      })
      .catch(err => {
        console.error("Error fetching users:", err);
        setMessageVisible(true);
      });
  }, []);

  const handleFollow = async (followeeUsername) => {
    // Handle follow functionality
    const response = await fetch(API_URL + '/follow', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        follower_username: username,  // The logged-in user's username
        followee_username: followeeUsername,  // The username of the user to follow
      }),
    });

    const result = await response.json();
    if (result.status === 'Follow successful') {
      alert('You are now following this user!');
    }else{
      alert('You already follow this user');
    }
  };

  const handleSearch = async () => {
    try {
      // Cambiar el parámetro de 'id' a 'username' en la URL
      const response = await fetch(API_URL + `/friends/search?username=${encodeURIComponent(searchId)}`);
      
      if (response.status === 404) {
        setFoundUser(null);
        alert('User not found');
        return;
      }
      
      const result = await response.json();
      setFoundUser(result.user || null);  // Guardar el usuario encontrado en el estado
    } catch (error) {
      console.error("Error fetching user:", error);
      alert('An error occurred while searching for the user.');
    }
  };

  return (
    <div className="section">
      <h2>Find Friends</h2>

      {/* Search for a user by username */}
      <input
        type="text"
        placeholder="Search by ID..."
        className="input"
        value={searchId}
        onChange={(e) => setSearchId(e.target.value)}
      />
      <button className="button" onClick={handleSearch}>Search</button>

      {foundUser && (
        <div className="result-item">
          <p><strong>Username:</strong> {foundUser.username}</p>
          <button className="button" onClick={() => handleFollow(foundUser.username)}>Follow</button>
        </div>
      )}

      {/* Display random users */}
      <div className="results">
        {users.map((username, index) => (
          <div key={index} className="result-item">
            <p><strong>Username:</strong> {username}</p>
            <button className="button" onClick={() => handleFollow(username)}>Follow</button>
            <hr />
          </div>
        ))}
      </div>

      {/* Hidden message if no users are available */}
      {messageVisible && (
        <p>Vaya, nadie se ha registrado aún a esta increíble red social :(</p>
      )}
    </div>
  );
}
